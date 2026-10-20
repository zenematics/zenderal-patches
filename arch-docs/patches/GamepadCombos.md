# GamepadCombos

- **Source:** `src/GamepadCombos/`
- **Ships:** *(no plugin — `SKSE/Plugins/ZenGamepadCombos.dll` + `ZenGamepadCombos.ini`)*
- **FormID block:** _(none)_

## What it does

**On a controller, LB sheathed/drew the weapon instead of attacking or blocking with the left hand.**
[reported by the curator 2026-10-19] Complete Controller Setup's Layout 133 binds LB to `Left
Attack/Block` and `A + LB` to `Ready Weapon` (`0x1000+0x0100` in `controlmap.txt`, `0x10000100` in
`ControlMap_Custom.txt`: modifier in the high word). Every copy of both files in the list carries those
values, so the data was right. The engine is the problem: **SSE 1.5.97 does not check a gamepad combo's
modifier.** A button bound both alone and as the second key of a combo resolves to one of the two whether
or not the modifier is held. Measured in game with Layout 133 [verified by the curator 2026-10-19]:

| Button | Alone (intended) | Combo (intended) | What the engine did |
|---|---|---|---|
| LB | Left Attack/Block | A + LB = Ready Weapon | Ready Weapon, alone **and** with A |
| D-pad Down | Hotkey8 | B + D-pad Down = Quick Map | Quick Map, alone |
| Back | Wait | B + Back = Tween Menu | Wait, so the combo is dead |
| RB | Right Attack/Block | A + RB = Shout | Right Attack, so the combo is dead (inferred) |

Which of the two wins isn't consistent: LB and D-pad Down got the combo event, while Back and RB got the
plain one. CCS presumably targets AE, where combos work. This is an inference; it hasn't been checked on AE.

**Fix:** an SKSE plugin that resolves every gamepad press itself. At `kDataLoaded` it reads the Main
Gameplay context of the winning `Data/Interface/Controls/PC/controlmap.txt`, overlays the gamepad block of
`Data/ControlMap_Custom.txt`, and keeps every button that has
at least one combo binding. With the list's files that is 8 buttons: LB, RB, Back, Start, LS, D-pad
Down/Left/Right. The custom map is binary: three blocks (keyboard, mouse, gamepad), each a 3-byte header and then one
5-byte entry (`u8` Main Gameplay index, `u32` big-endian key) per event whose remap flag for that device is
1. The engine drops the whole file when any count disagrees with `controlmap.txt`, so the plugin checks the
total size against the flags and ignores the file in the same case. With the list's files the counts are
27/25/12, which makes the file 329 bytes.

On each press of one of them in the gameplay context, it picks:

1. the combo binding whose modifier is held, else
2. the plain binding, else
3. nothing (an empty user event).

The choice is latched on the press and reused for that press's held and up events, so a release always
reaches the handler that saw the press, even if the modifier was let go first. It is applied in the
`InputEvent*` sinks of `MenuControls` and `PlayerControls` (vfunc `0x01` of their first vtable), before
the originals compare `userEvent`. Both hooks run the same idempotent code, so whichever the engine calls
first does the work. Mod sinks register later (at `kInputLoaded` or after) and see the corrected event.
The plugin never touches menu contexts, the keyboard or the mouse.

**What the modifier still does.** Pressing A still activates and holding B still sprints, because
those are their own plain bindings and fire first. The plugin only decides what the *second* button does.

**Log.** `…\My Games\Skyrim Special Edition\SKSE\ZenGamepadCombos.log` lists the table it built, then the
engine's own gamepad mappings for the same buttons (`inputKey`/`modifier`/`linked`, to learn what 1.5.97
actually stores). With `LogPresses=1` it also logs every press as `press 0x0100 held [0x1000]: engine
'Ready Weapon' -> 'Ready Weapon'`. Set `LogPresses=0` once it is verified.

**Limits.** In-game remaps made in the Controls menu take effect after a restart, since the table is read
from the files at load. It doesn't cover a combo whose *first* key is the one that matters. Every combo in
the list today uses A or B as the modifier.

Built 2026-10-19, **not yet verified in game**.
