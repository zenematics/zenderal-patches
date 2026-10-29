# SpellAimTrace → `ZenSpellAimTrace.dll`

**Testing tool, not part of the list.** MO2 mod `Zenderal - Spell Aim Trace`; disabled 2026-10-29 by
renaming the DLL to `.mohidden`. Built for [`ThirdPersonSpellAim`](ThirdPersonSpellAim.md).

## What it logs

Read-only; nothing is written back. Log: `SKSE/ZenSpellAimTrace.log` next to the other SKSE logs.

- **Every projectile the player launches** (Detours on `Projectile::Launch`, ID 42928/44108): base
  projectile, spell, `LaunchData` origin/angles/flags (`autoAim`, `useOrigin`, `desiredTarget`), the
  player's angles, both magic nodes, the camera root position and forward, and the engine's
  `CrosshairPickData` target and collision point. For each it logs the angle between the launch
  direction and the direction from the origin to that point.
- **The first 4 `UpdateImpl` calls** (vfunc `0xAB`) of each tracked Beam/Missile/Cone projectile:
  position, angle, velocity.
- **Every `AddImpact`** (vfunc `0xBD`) of a tracked projectile: the ref, location, collision layer.

`CrosshairPickData::collisionPoint` is garbage when the pick has only a target and no fresh hit
(seen with Firebolt casts). Trust the target ref, not the point, in those lines.

## Build

`build.cmd` (VS 2026 Build Tools, vcpkg with Detours; repo-root `lib/CommonLibNG`). Output copied to
`compiled/`.
