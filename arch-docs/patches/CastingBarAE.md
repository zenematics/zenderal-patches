# CastingBarAE

- **Source:** `src/CastingBarAE/` — zax-ftw/CastingBar 3.0.0 (GitHub, Apache-2.0, `LICENSE` kept) + Zenderal changes;
  CommonLibSSE-NG from the repo-root `lib/`, `build.cmd`
- **Ships:** `SKSE/Plugins/CastingBar.dll` (AE, Address Library), MO2 mod `Zenderal - Casting Bar AE`, sorted
  **above** `Casting Bar` and `Casting Bar SKSE Menu Framework`. Still needs `Casting Bar` (Nexus 80455) for its
  `interface/CastingBar_*.swf` and `CastingBar.ini`.
- **FormID block:** none (no plugin)

## Why

`Casting Bar SKSE Menu Framework` 3.0.0 (Nexus 173070, a UI fork of zax's 3.0, "only tested on 1.5.97") froze the game
at startup on 1.7.104: `skse64.log` ends at `loading plugin "CastingBar"`, no `CastingBar.log`, no crash log.
**[verified 2026-10-23]** Its CommonLibSSE-NG (flatrim) reads the Address Library through `IDDatabase::header_t::read`,
which compares the file's format with the expected 1 (SE) or 2 (AE) — `cmp dword ptr [rbp-49h],ebx` /
`jne` → "Unsupported address library format". 1.7.104's `versionlib-1-7-104-0.bin` is **format 5**. The first
relocation is resolved inside `SKSE::log::log_directory()` (the game's My Games folder name), so the fatal
`report_and_fail` box fires before the log exists — and opens behind the fullscreen window, which looks like a hang.
The original Casting Bar 3.1 (no SMF page) loads fine; it is closed source and newer than the GitHub 3.0.

No source exists for the SMF fork, so this rebuilds zax's 3.0 source against the repo's NG (which reads format 5)
and re-adds what the fork added:

- **SKSE Menu Framework page** `Casting Bar/Settings`: the three enable toggles, per-widget position/scale sliders,
  a "Show for positioning" checkbox per widget (holds it at 60%), Save / Reload. Bound by `GetProcAddress` on the
  few `SKSEMenuFramework.dll` exports it needs (`AddSectionItem`, `igCheckbox`, `igSliderFloat`, …), as Thiago099's
  SDK header does; skipped cleanly when SMF is absent.
- **Per-widget layouts** `[Spell]` / `[Shout]` / `[Bow]` (`PositionX/Y`, `ScaleX/Y`, the fork's keys). The old
  `[Position] Widget*` values seed all three when a section is missing.
- **Ultimate Immersion Toggle:** `HideWithHUD = true` (`[General]`). UIT hides the HUD by setting
  `"HUD Menu"`'s `_root._alpha` to 0 (`Luca_HideUIConfigMenu.HideHUD`, list default `bHUD_Menu = 1`); the widget
  reads that every frame and hides with it. No change to UIT's script.

## AE addresses (checked against 1.7.104)

Resolved through the format-5 Address Library and the 1.7.104 exe: `14220` (GetObjectTypeId) `0x1D74A0`,
`26417` (GetWeaponSpeed) `0x41EF20`, `44108` `0x7F9300` with an `E8` call at `+0x5D6` (the arrow-power
`write_call`). The `PlayerCharacter` vtable hook (`DrawWeapon`, slot `0xA6`) is unchanged from 3.0/3.1.

## Status

Built 2026-10-23. Unverified in game.
