# WolfMountTurning

- **Source:** `src/WolfMountTurning/` (generated: `tools/01-build-wolf-mount-turning.py`; `tools/00-scan-mount-movement.py`
  shows who wins the mount races and movement types; `tools/02-verify.py` checks the build against the live winner)
- **Ships:** `Zenderal - Wolf Mount Turning.esp` (ESL, HEDR 1.7, masters Skyrim/Update/FS only). Deployed 2026-11-12 as
  its own MO2 mod `Zenderal - Wolf Mount Turning`. **Must load after `Enderal SE - Gameplay Overhaul.esp` (EGO).**
  Candidate for the next Patch Collection merge.
- **FormID block:** none (overrides only)
- **Owns:** race `HorseFluteWolfMountRace 0450F7` (EGO's record verbatim + two movement-type overrides)
- **Status:** built, verified against the live winner, **verified in game 2026-11-12** (curator: Father Shadow turns
  when ridden; ticked in Ultra, plugin after EGO).

## Why

Player report (Junebug, 2026-11-12): *"The mount you get at the end of the questline - Shadow of Transience - only
goes in one direction and cannot turn"*. The mount is **Father Shadow** (`_00E_FS_NQR05_FatherShadow 0450F9`), the
Rhalâta questline's reward (FS_NQR01–05, siding with the Father): a wolf, race `HorseFluteWolfMountRace 0450F7`,
graph `Actors\Canine\WolfProject.hkx`.

## Cause

A ridden mount moves on the movement types (MOVT) its behaviour graph names: for the wolf graph `WolfDefault` and
`WolfRun`, i.e. `Wolf_Default_MT 055D28` and `Wolf_Run_MT 0EA64B` (the ride ran at 666.7 = 555.56 × SpeedMult 1.2).
EGO wins both and leaves out `RotateWhileMovingRun`:

| MOVT | Stock (Skyrim.esm) | EGO (winner) |
|---|---|---|
| Rotate in place walk/run | 180 / 270 °/s | 180 / 220 °/s |
| **Rotate while moving** | **360 °/s** | **0** |

So the moment the wolf moves, the engine allows it no turn. Every key (W/A/S/D) makes a ridden mount move, so it only
ran straight. Wild wolves are what EGO tuned this for; they keep it.

How it was found (all in [`ZenMountTrace`](ZenMountTrace.md)): the input arrives, the player-controls movement agent
(ID 42162) gives the mount a desired heading, but the mount's own `rotationSpeed.z` is written 0 every frame by its
movement controller (ID 37356 +0x3F4). The controller's arbiter (ID 92401) clamps the output against the current
movement type's speeds (`1226ED0` / `1227060`). TDM, SmoothCam, the wolf graph, Pandora and the race's own fields
were ruled out on the way (see the trace doc). Horses: their movement types (`Horse_Default_MT`, `Horse_Sprint_MT`,
`NPC_Horse_MT`, `Horse_Fall_MT`, `Horse_Swim_MT`) are untouched in the list and turn 45–270 °/s, so this cause does not
reach them. Reports that horses fail too are not confirmed in game.

## Fix

The race's own per-movement-type speed overrides (RACE `MTYP` + `SPED` pairs; Spriggit `MovementTypes`, as vanilla
cows, chickens and atronachs use), on the mount race only. One override per wolf movement type, with EGO's speeds and
in-place turn rates, and stock's turn-while-moving rate. The MOVT records stay EGO's. Spriggit field names in the
override: `RotateWalk` / `RotateRun` = in place, `Unknown` = while moving, in **radians** (the MOVT records themselves
are in degrees).

## Verification

`tools/02-verify.py` decodes the built race and the load order's winner (EGO): 73 ordered subrecords, the 5 movement
type names and 12 attacks are identical. Spriggit writes `MTNM` names and attacks in its own sorted order; ATKD/ATKE
pairs stay together, and the engine looks attacks up by event. The only additions are the two `MTYP`/`SPED` pairs
(`055D28`, `0EA64B`, while-moving 360 °/s). Nothing else in the load order overrides `0450F7`.

## In game

Tick `Zenderal - Wolf Mount Turning` in MO2 (plugin anywhere after EGO), summon or ride Father Shadow
(`player.placeatme 0450F9` for a test), run, and steer with A/D and the mouse. Rerun 00 → 01 → 02 after an EGO update.
