# ZenKeyTrace

- **Source:** `src/ZenKeyTrace/` (CommonLibSSE-NG, `build.cmd`)
- **Ships:** `SKSE/Plugins/ZenKeyTrace.dll` (AE, Address Library; no plugin)
- **FormID block:** none

## Why it exists

The Stances hotkeys (F1–F4, and `[ ' ; ]` that Gamepad++ sends on D-pad long presses) are dTry's Key Utils
key traces: `SKSE/Plugins/dtryKeyUtil/config/custom/Stances.ini` binds each key to a `stances_switchspell_*`
ability of `Stances - Dynamic Weapon Movesets SE.esp`. Three mods ship a `DtryKeyUtil.dll` **[verified 2026-10-21]**:

| Mod | Build | Reads `config/custom`? | On 1.7.104 |
|---|---|---|---|
| dTry Plugin Updates 1.0.3 | 1.5.97 | yes | off (SE only) — this was the winner before the AE migration |
| dTry's Key Utils AE 1.1 (Nexus 69944, 2022) | AE, old Address Library | yes | **refused by SKSE 2.3.1**: "must be recompiled for new address library" |
| PaulMix's dTry Key Utils extend 3.3 (Nexus 141040) | AE | **no** — a rewrite; no `KeyTrace_*` / `config\custom` strings in the DLL | loads; does the movement-direction trace (Keytrace.esp MGEFs `801`–`804`, used by Dynamic Dodge, FHiS, Patch Collection) |

So after the update the stance keys did nothing. ZenKeyTrace re-implements only dTry's key-trace part, with a
different DLL name so it runs alongside PaulMix's.

## Behaviour (from D7ry/DtryKeyUtil `inputEventHandler.cpp`, `inputHandler/inputTracer.cpp`)

- At `kDataLoaded`, every `*.ini` in `Data/SKSE/Plugins/dtryKeyUtil/config/custom` (MO2's winning copies) is read with
  SimpleIni multi-key; sections `KeyTrace_EventID_Keyboard` / `_Mouse` / `_GamePad` (`<name> = <id>|<formID>|<plugin>`)
  and `KeyTrace_userEvent` (`<name> = <user event>|<formID>|<plugin>`).
- IDs: keyboard DX scan code, mouse button + 256, gamepad button index + 266 (dTry's `GetGamepadIndex` order).
- Button down → `AddSpell` on the player, button up → `RemoveSpell`. Events are ignored while the game is paused.
- One deliberate difference: dTry stops processing the event chain at the first non-button event; this skips it.
- Logs every binding to `My Games/Skyrim Special Edition/SKSE/ZenKeyTrace.log`.

## Status

Built 2026-10-21, deployed as MO2 mod `Zenderal - Key Trace`. Unverified in game.
