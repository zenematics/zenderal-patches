# OCPASecondKey

- **Source:** `src/OCPASecondKey/` (`src/main.cpp`, `build.cmd`; compiled DLL committed in `compiled/`)
- **Ships:** `ZenOCPASecondKey.dll` + `ZenOCPASecondKey.ini`, MO2 mod `Zenderal - OCPA Second Key`
- **FormID block:** _(none — no plugin)_

## What it does

**RT and Mouse 4 both power attack** (curator request, 2026-10-25). One Click Power Attack NG reads one key,
`[General] iKeycode` in `Data/MCM/Settings/OCPA.ini`. The list sets it to Mouse 4 (259) in `Zenderal - Input
Defaults`, so the controller's RT did nothing, and switching meant editing the MCM each time. Both the installed build
("One Click Power Attack AE 1.7 Test", Nexus 60878) and the public source (jarari/OneClickPowerAttack, no license; the
Apache-2.0 1.7.104 port DeadOnKeyboard1/OneClickPowerAttack_1.12.3_AE_1.7.104.0-Update) take a single key. Rebuilding
OCPA would mean redistributing modified unlicensed code, so this is a separate plugin, written here.

On a press of its own key (`iKeycode` in `ZenOCPASecondKey.ini`, default **281 = RT**) it does what OCPA's input
handler does for its key, read from that port's `src/Main.cpp`:

- **Conditions:** `canProcessPowerAttack()`: not paused, no Dialogue Menu, not mounted, not in a kill move,
  sit/sleep state normal, and stamina > 0 unless `bAllowZeroStamina`. Then OCPA's `bOnlyDuringAttack` (melee
  attack state `kDraw`–`kBash`), `iModifierKey` (< 2 = none) and `bSkipModifierDuringCombo` rules.
- **Action:** OCPA's `PowerAttack()`: when `bInJumpState` or `IsBlocking`, `ActionRightAttack 0x13005` and then
  `ActionRightPowerAttack 0x13383` 200 ms later. Otherwise `ActionRightPowerAttack`. Both go through OCPA's
  `PerformAction` (`TESActionData` into ID 40551/41557; on 1.7.104, 41557 = `0x78DB80`).
- **Queue:** a refused power attack is retried each frame for `fQueueExpire` (0.2 s) when `bQueuePowerAttack` is on.
  OCPA retries only on `MCO_PowerWinOpen/Close`; the action still only succeeds when the game allows it.

All of OCPA's settings are read from OCPA's own ini: the user's `MCM/Settings/OCPA.ini` first, then
`MCM/Config/OCPA/settings.ini`, then OCPA's defaults. They're re-read on each save load and when the Journal (MCM)
closes, the same times OCPA reloads. If the second key equals OCPA's key, the plugin stays idle. Key codes are
OCPA's: keyboard DX scan code, mouse 256 + button, gamepad 266–281. The delayed and queued attempts run from a
`PlayerCharacter::Update` hook (vfunc `0xAD`, the same one ZenBlockReleaseFix uses on 1.7.104).

Built against the repo-root `lib/CommonLibNG`, SE + AE. Build with `src/OCPASecondKey/build.cmd` from a plain PATH:
an inherited PATH entry containing `&` breaks `vcvars64.bat`.

## Status

Built and installed in Ultra 2026-10-25, sorted above One Click Power Attack NG. **Unverified in game.** Check:
RT power attacks while Mouse 4 still does, and `ZenOCPASecondKey.log` logs `Second key 281 pressed … -> power attack`.
