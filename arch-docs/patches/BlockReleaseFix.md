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

**1.0.1 → 1.0.2: map gamepad codes too.** [verified by the user 2026-10-17: holding LT flickered the
block] 1.0.1 assumed controller blocking ran through vanilla `Left Attack/Block`. It does not: the
controller controlmap binds that to **LB** (`0x0100`), and the list blocks on **LT** through DWP's
`ParryKey2 = 280` (set by Custom Keybinds / CCS; SKSE numbering 266 = D-pad up … 280 = LT, 281 = RT).
1.0.1 ignored every gamepad event that was not a vanilla attack, so a held LT read as "no block key
held" and was cancelled every `kRetryMs` (500 ms), the same flicker as 1.0.0's. 1.0.2 converts the
engine's XInput mask / trigger code (`0x9`/`0xA`) to SKSE's number before comparing it with `ParryKey`
and `ParryKey2`.

**Limits.** A mod that starts a block from script with no key held would have it
ended after `GraceMs`; none is known in the list.

Built and deployed 2026-10-13; 1.0.2 built and deployed 2026-10-17, **not yet verified in game**. Build note: `build.cmd` falls back to `vswhere` when the BuildTools path is absent (this machine has VS 18 Community); clone CommonLibSSE-NG into `lib/CommonLibNG` first.
