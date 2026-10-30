# RemoteCastAimFix → `ZenRemoteCastAim.dll`

**Ships:** one SKSE plugin, MO2 mod `Zenderal - Remote Cast Aim Fix`. No plugin file, no edits to Hit Where You
Aim. Source `src/RemoteCastAimFix/`, built with its `build.cmd` (shares the CommonLibSSE-NG clone in `lib/`).

## Problem (2026-10-29)

After [Hit Where You Aim](ThirdPersonSpellAim.md) went in, Prophecy's **Smite** beams of light no longer struck
the enemies around its target. The curator confirmed on 2026-10-30 that the beams still fire but are misplaced,
and that HWYA is what misplaces them.

## Cause

Smite places Holy Templar's `ZP_Holy_LightshaftActivator_Player 000A46`. The activator's
`_LIP_LightshaftSkyboltActivatorScript` (read from its bytecode with `tools/pexdis.py`) does three things:

1. Places 9 markers scattered up to 512 units around the target.
2. Places a spawner 80 units above the target.
3. Because `IsPlayerCast` is on, fires `ZP_Holy_LightshaftScatterProjSpell 000A39` (a Cone projectile) from
   the spawner at each marker, with `LightshaftSpell.RemoteCast(Spawner, Game.GetPlayer(), marker)`.

The player is the blamed actor, so the projectile's shooter is the player. Wrath of the Heavens (`000A44`)
fires its sky-bolts the same way.

HWYA has four projectile hooks (`Hooks.h`). The one that moves these beams is `ProjectileInitHook`. On
1.7.104 it sits on the call at ID 44222 +0x78A, to the projectile's initialisation (ID 44184). For every
projectile whose shooter is the player, it saves `data.angle` before that call and writes it back after.
Its source comment says this is because "TDM overrides the data here". A remote cast's projectile turns
toward its target during that initialisation, so the write-back threw away the aim at the scattered markers.

## Fix

At `kPostLoad`, after HWYA's `SKSEPluginLoad` has written its hook, the plugin writes its own call at the
same site and keeps HWYA's as the next one. A projectile is treated as a remote spell when all of these hold:

- its shooter is the player;
- it has a spell and no weapon or ammo source;
- it starts more than 64 units from every player magic node (left, right, other, instant) and from the
  head in both 3D trees.

Such a projectile gets only the game's own initialisation, as before HWYA. Everything else goes through
HWYA as before.

The first 30 remote projectiles are logged to `ZenRemoteCastAim.log`, each with its kept angle and the angle
HWYA would have written back. The load line says whether the call led to HWYA or to the game's own function.

## History

**1.0.0 (2026-10-29)** hooked HWYA's `PlayerProjectileCalculateLaunchAngleHook` instead, at the
launch-angle call ID 44200 +0x201. In game it logged no remote launches: the game makes that call only for
auto-aimed launches. The beams stayed misplaced.

## Status

1.1.0 built 2026-10-30. **Unverified in game**: check that Smite's beams strike around the target, that the
log lists them, and that third-person Consecrate Dead still hits the corpse under the crosshair.
