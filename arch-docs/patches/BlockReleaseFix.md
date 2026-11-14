# BlockReleaseFix

- **Source:** `src/BlockReleaseFix/`
- **Ships:** *(no plugin — `SKSE/Plugins/ZenBlockReleaseFix.dll` + `ZenBlockReleaseFix.ini`)*
- **FormID block:** _(none)_

## What it does

**The player sometimes stayed stuck in the block animation after letting go of block, until the block
key was tapped again.** [verified by the user 2026-10-13: a tap always frees it] In this list, blocking
goes through **Dual Wield Parrying SKSE 1.7.0** (`ParryKey = 258`, right click, from `Zenderal - Personal
Keybinds`; the list default is 261 = Mouse 5). Its `src/InputEventHandler.cpp` [upstream] is purely
event-driven. On a key-up it sets `wantBlocking = 0` and sends `blockStop` only `if (isBlocking)`, and all
of that sits behind early returns. The handler ignores the event entirely when the game is paused, a
menu is open, fighting controls or `attackBlockHandler->inputEventHandlingEnabled` are off, the weapon
state is not `kDrawn`, the knock state is not normal, the player is flying or in a killmove, or the
`IsBlocking` read fails. Nothing re-checks afterwards. So a release during any of those states, or while
`IsBlocking` briefly reads false during a block-hit, timed-block or counter clip, is lost. The tap fixes it
because the press passes the "already blocking" check and its key-up sends the missing `blockStop`.

**Fix:** an SKSE plugin that tracks the block keys itself, through a `BSInputDeviceManager` sink, which sees
every key-up whatever DWP's gates say. The watched keys are DWP's `ParryKey`/`ParryKey2`, read from DWP's
own ini through the VFS (keyboard = DX code, mouse = button + 257), plus the vanilla `Left/Right
Attack/Block` user events on every device. On each `PlayerCharacter::Update` (vfunc `0xAD`): if no block
key is held, at least `GraceMs` (200) has passed since the last key-up, and `IsBlocking` or `wantBlocking`
is still set, it clears `wantBlocking` and sends `blockStop` (`IsBlocking` only). That is exactly what DWP
would have done. Retries are spaced 500 ms apart. Each stop it forces is logged to
`…\My Games\Skyrim Special Edition\SKSE\ZenBlockReleaseFix.log` with the weapon and knock state, which
shows which gate dropped the release.

**1.0.0 → 1.0.1: never read DWP's ini with `GetPrivateProfileInt`.** [verified 2026-10-13] DWP's shipped
ini starts with a UTF-8 BOM, which sticks to the first section header, so `[DualWieldParrying]` was never
found and `ParryKey` read as 1000000. 1.0.0 therefore treated a held right click as "no block key held"
and cancelled the block every 500 ms, so holding block flickered. 1.0.1 parses the ini itself, skipping
the BOM, and stays inert (logs a warning) if `ParryKey` can't be read. Check the startup line in the
log: `DWP ParryKey=258`.

**1.0.1 → 1.0.2: gamepad DWP keys.** [verified from the log 2026-10-25] On controller, holding LT made the block
stop and restart every 500 ms. The log showed `Ended stuck block … N ms after last block key-up` every 0.5 s while
LT was held. Complete Controller Setup binds vanilla `Left Attack/Block` to LB, not LT; LT blocks through DWP's
`ParryKey2 = 280`, and 1.0.1 only decoded DWP keys from keyboard and mouse. 1.0.2 maps gamepad buttons to DWP's
266–281 numbering, copied from DWP's own switch (`lib/rebuilds/DWP/src/InputEventHandler.cpp:62-114`). Built with a
plain PATH (an inherited PATH entry with `&` breaks `vcvars64.bat`), committed in `compiled/`, and deployed to
`Zenderal - Block Release Fix` and `Zenderal - Patch Collection` (which carries a copy). 1.0.1 is backed up in
`E:/Zenderal-backups/2026-10-25-blockreleasefix-1.0.1`.
PR #4 (merged to `main` 2026-10-17) had fixed the same bug independently (the engine's XInput mask / trigger code converted to SKSE's number); merging `main` on 2026-11-01 kept this build, the one deployed in the list (both MO2 copies match `compiled/`).

**1.1.0 (2026-11-13): menu equips in first person.** [cause verified in trace; fix unverified in game] The curator's
first-person dual daggers still locked up after [`FirstPersonDrawFix`](FirstPersonDrawFix.md): after equipping a
dagger from the inventory, attacks and block did nothing until a 3rd → 1st person camera switch, and the screen showed
bare forearms. [`ZenParryTrace`](ZenParryTrace.md) 1.5.0 (log 2026-11-13 19:02–19:21):

- An inventory equip with weapons out sends `WeapOutRightReplaceForceEquip` / `WeapOutLeftReplaceForceEquip`
  into both graphs while the game is paused. The third-person graph runs in the menu (the inventory shows it), and
  its `BeginWeaponDraw` / `weaponDraw` arrive at once. The first-person graph starts its draw there too, but none of
  its events arrive while the menu is open.
- Lock-ups at 19:05:54 and 19:13:45 (right dagger then left dagger, in one menu visit): after the menu closed, the
  first-person graph sent only `WeapEquip_Out`, 0.93 s later. That is the end of a draw that had already been playing
  for ~0.4 s, i.e. since the second equip. `IuEquip`, `BeginWeaponDraw` and `weaponDraw` never came, and every
  `attackRelease` after that was refused.
- Equips that worked (19:05:24, 19:11:59): the game sent the equip event once more as the menu closed. The first-person
  draw then restarted live, and all its events arrived.

So the game only sometimes repeats the equip after the menu. 1.1.0 makes it always happen. It hooks the player's
`NotifyAnimationGraph` (`VTABLE_PlayerCharacter[3]`, slot 1) and remembers an equip event (`WeapOut*ReplaceForceEquip`,
`WeapEquip`, `WeapSoloEquip`, `WeapLeftEquip`) sent while `UI::GameIsPaused()`. A right-hand replace is kept over later
ones, as the game's own repeat is that event. A live equip event clears it. On the second player update after the game
runs again, if it is still pending, the camera is first person and the weapon state is drawing or drawn, it sends the
event once more through the same call. It logs `Menu equip: sent … again`. `[MenuEquip] Enabled=0` turns it off.
Third person is untouched (its graph got its events). In first person the third-person graph replays its draw unseen,
as it does when the game repeats the event.

**Limits.** A mod that starts a block from script with no key held would have it
ended after `GraceMs`; none is known in the list.

Built and deployed 2026-10-13; 1.0.2 built and deployed 2026-10-25; 1.1.0 built and deployed into
`Zenderal - Patch Collection` 2026-11-13 (no standalone `Zenderal - Block Release Fix` mod is installed any more). **1.0.2 not yet verified in game.** Build note: `build.cmd` falls back to `vswhere` when the BuildTools path is absent (VS 18 Community); clone CommonLibSSE-NG into `lib/CommonLibNG` first.
