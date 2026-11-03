# ImprovedCameraSheatheFix

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/ImprovedCameraSheatheFix/`
- **Ships:** *(no plugin — `SKSE/Plugins/ZenICSheatheFix.dll`)*
- **FormID block:** _(none)_

## What it does

**Every first-person sheathe ended with a small camera snap upwards, on all weapons.** Not an animation, setting or other mod (bisected in game 2026-10-11: OAR clips forced vanilla, IC-VanillaAnims off, head bob off, First Person Combat event off, First Person Overhaul off, Adjust Player Scale off, First Person Height Fix SKSE off — all still snapped; IC disabled — gone). Cause is hard-coded in Improved Camera SE 1.1.2.4228 `ImprovedCameraSE::TranslateCamera()` (ArranzCNL/ImprovedCameraSE-NG, source matches the shipped build): `upDisplacement = NPCEyeBone.local.z + HighHeelsOffset` (0 while sneaking) is zeroed `if (IsWeaponDrawn())`, so the camera drops by the eye-bone height while drawn and jumps back the frame the weapon state leaves Drawn/WantToSheathe/Sheathing. Head bob only changes how big it looks. Fix: SKSE plugin that on `kPostLoad` verifies 24 bytes at `ImprovedCameraSE.dll+0x78276` and NOPs the inlined `xorps xmm11,xmm11` at `+0x78282` (`0F 1F 40 00`) — the raise now always applies (the curator chose "always raised" over "never"). Other IC builds are logged and left alone; re-derive the RVA from IC's shipped `.pdb` with `dumpbin /disasm` (symbol `?TranslateCamera@ImprovedCameraSE@ImprovedCamera@@AEAAXXZ`) after any IC update. Log: `…\My Games\Skyrim Special Edition\SKSE\ZenICSheatheFix.log`. Also learned: `First Person Height Fix SKSE` duplicates IC's `bAdjustPlayerScale` (its author says not to run both) and was disabled in the same session. Built and deployed 2026-10-11, not yet verified in game.

## Status 2026-11-03: inert on Improved Camera 2.0

The list moved to Improved Camera SE 2.0.0.2226 (Wabbajack CDN copy, `authored-files.wabbajack.org/ImprovedCameraSE-2.0.0.2226-RelWithDebInfo.zip_d9f12fc4-…`). The plugin's byte check fails there and it patches nothing (`ImprovedCameraSE.dll bytes at RVA 78276 do not match build 1.1.2.4228 - NOT patched`). The curator has seen no sheathe snap on 2.0 so far, so it is not being re-derived. Its DLL still ships in Patch Collection (harmless; it also logs camera state every few seconds); drop it at the next Patch Collection rebuild unless the snap returns.
