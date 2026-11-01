# AimFacingLock → `ZenAimFacingLock.dll`

**Ships:** one SKSE DLL + `SKSE/Plugins/ZenAimFacingLock.ini`. No plugin. MO2 mod `Zenderal - Aim Facing Lock`.

## Problem (2026-10-21)

Aiming a bow/crossbow/musket in third person and pressing a strafe key with forward (W+A) swung the
body, and the weapon, off the crosshair, then back. Ruled out:

- **TDM:** the list runs `uDirectionalMovementDrawn = 1` (Vanilla Style). In TDM's source
  (`DirectionalMovementHandler.cpp`, `UpdateFacingState`/`UpdateFacingCrosshair`) Vanilla Style forces
  face-crosshair while moving, and while `_bIsAiming` with no camera offset TDM leaves the heading
  alone. Turning on `bFaceCrosshairInstantly` did **not** change it in game.
- **DMK** only writes graph variables (`DirecionalCycleMoveset`, …); it never rotates the player.
- **Offset Movement Animation** is only used by Helmet Toggle.

## Mechanism

Hooks `PlayerCharacter::Update` (vtable 0, vfunc `0xAD`). After the original runs, on every frame the
player aims in third person (`kBowDraw`, `kBowDrawn`, `kBowReleasing`, `kBowReleased`; `kBowAttached`
for bows only, since for a crossbow/musket it is the reload), the heading is set to the camera yaw
(`angle.z + ThirdPersonState::freeRotation.x`, the sum TDM aims with) and `freeRotation.x` zeroed, so
the camera does not move. Not while sprinting or mounted.

`Log=1` writes each aiming frame whose heading moved more than `LogThresholdDegrees`, split into
*outside* (since our last correction) and *inside* (during `Actor::Update`). **If the turn is still
visible and the log is quiet, the heading never moved: the turn is in the animation (pelvis/spine)
and this plugin cannot lock it.** `Enabled=0` keeps the log for comparison.

## Status

Built 2026-10-21, deployed to `E:\Zenderal\mods\Zenderal - Aim Facing Lock`. **Unverified in game.**
