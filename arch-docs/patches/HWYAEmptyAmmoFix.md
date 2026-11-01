# HWYAEmptyAmmoFix → `ZenHWYAEmptyAmmo.dll`

**Ships:** one SKSE plugin, MO2 mod `Zenderal - HWYA Empty Ammo Fix`. No plugin file, no edits to Hit Where You
Aim. Source `src/HWYAEmptyAmmoFix/`, built with its `build.cmd` (shares the CommonLibSSE-NG clone in `lib/`).

## Problem (2026-10-30)

Firing the last bullet crashed the game (a player report; the curator reproduced it). Crash Logger:
`EXCEPTION_ACCESS_VIOLATION` at `HitWhereYouAim.dll+0x2551C`, reading address `0x110`, in
`Hooks::PlayerSetAimPitchHook::PlayerGetAimPitch` (`Hooks.cpp:358`), called from the game's ID 37356 +0xC3F.

## Cause

HWYA hooks the call in ID 37356 (+0xC3A in 1.7.104) to the player's aim-pitch setter, ID 39880. That is the
angle the third-person aiming pose uses. (Found by pattern-matching HWYA's own injection signature in the
unpatched `SkyrimSE.exe` and looking the callee up in the Address Library.) In its source:

```cpp
if( Settings::IsAutomaticPitchEnabled() )
{
    auto projectile = player->GetCurrentAmmo()->GetRuntimeData().data.projectile;
```

This runs while the weapon is drawn and the attack state is between `kBowDraw` and `kBowFollowThrough`, with
no null check on the ammo. The last arrow or bullet unequips the ammo while the attack state is still in that
range, so it reads `nullptr + 0x110` (`r15 = 0x110`, `rbx = 0` in the log). The same applies to bows and
crossbows, and to drawing with no ammo at all. Automatic pitch is on in the list (the Easy preset).

## Fix

At `kPostLoad`, after HWYA's `SKSEPluginLoad` has written its hook, the plugin writes its own call at the
same site and keeps HWYA's as the next one. On each call:

- **The player's process, weapon drawn, attack state in HWYA's range, no ammo equipped:** the plugin calls
  only the game's function, ID 39880, as before HWYA. The aim pose keeps the game's own pitch for those
  frames.
- **Anything else:** HWYA runs as before.

The first 10 skipped frames are logged to `ZenHWYAEmptyAmmo.log`. The load line says whether the call led to
HWYA or to the game's own function.

A rebuilt HWYA with a null check would be the upstream fix. The list keeps HWYA untouched (see
[`RemoteCastAimFix`](RemoteCastAimFix.md), which chains the same way at another of its hooks).

## Rerun

Rebuild after an HWYA update only if its injection site moves. The load line then reports "HWYA not
installed" or an error. If HWYA adds the null check itself, retire this plugin.

## Status

Built and deployed 2026-10-30. **Verified in game 2026-10-30**: firing the last musket ball no longer crashes.
