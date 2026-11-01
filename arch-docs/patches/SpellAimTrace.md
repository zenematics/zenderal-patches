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

**1.1.0 (2026-11-01)**, for first-person musket shots landing above the crosshair dot
([`FlintlockOverhaul`](FlintlockOverhaul.md), aim down sights):

- Arrow-type projectiles (bolts, Ordo's musket balls) get the update and impact hooks too.
- Each launch also logs the rendering camera (`Main::WorldRootCamera`), the launch origin in the camera's
  frame, and where the first-person rig's `Camera1st [Cam1]` and `Weapon` nodes sit in it (Improved Camera
  may place the camera away from `Camera1st`).
- Each impact logs its offset from the **launch-time** crosshair ray: units out, units/degrees above and right.
  A constant angle over distance means a tilt; a constant height means a wrong launch point.

**1.2.0 (2026-11-01)** chains after Hit Where You Aim on the auto-aim launch-angle call (ID 44200 +0x201, the
site [`RemoteCastAimFix`](RemoteCastAimFix.md) 1.0.0 found; installed at kPostLoad) and logs its launch node,
`origin` argument (HWYA aims from it, or from the node when it is null) and the angle before and after HWYA,
against the camera's forward.

1.1.0 findings (22 musket shots, ADS build): the ball spawns at the first-person `NPC R MagicNode [RMag]`, which
DAR Rifles' clips park ~88 units out (local translation 9.6, -15.1, 89.7 from the hand), 2 right / 2 up of the
crosshair ray; it flies 0.2-0.33 deg above the camera's forward, landing +1-2 units high at ~270 units and
+15-19 at ~3000. The HUD dot is exactly at screen centre (measured in the curator's 3360x1440 recording). The
first-person rig's `Camera1st` sits exactly at the render camera; the render camera looks 2.5 deg higher than the
player's own pitch.

1.0.0's DLL is in `E:/Zenderal-backups/2026-11-01-spell-aim-trace-1.0.0/`. The MO2 mod now holds 1.1.0 unhidden;
it stays off by being unticked in the profile.

## Build

`build.cmd` (VS 2026 Build Tools, vcpkg with Detours; repo-root `lib/CommonLibNG`). Output copied to
`compiled/`.
