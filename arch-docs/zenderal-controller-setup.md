# Zenderal Controller Setup

How to add full Xbox-controller support to the Zenderal list (Enderal SE, engine **1.5.97**),
reproduced from a working install. Three mods off Nexus, one INI value, and one ready-built mod
from this repo carrying the Enderal-specific tweaks — everything Wabbajack-compilable, nothing
edited inside third-party mods.

## 1. Why this needs care on Enderal

1. **The list ships the gamepad disabled.** `EnderalPrefs.ini` carries `bGamepadEnable=0` — and
   the engine reads this setting from the **`[MAIN]` section, not `[Controls]`** where
   launcher-style INIs show it. A `=1` placed in `[Controls]` (or `[General]`) is silently
   ignored; only `[MAIN]` works.
2. **Enderal runs SSE 1.5.97, so every SKSE DLL must be a pre-AE build.** The current main file
   of Auto Input Switch is AE-only: SKSE 2.0.20 rejects it with
   `does not appear to be an SKSE plugin` in `skse64.log`, and the game runs fine without it —
   input switching just never works.
3. **1.5.97 is one-input-at-a-time.** In gamepad mode the mouse is dead and vice versa. Auto
   Input Switch is what makes both usable; without it a controller user gets stuck in menus with
   no cursor (character creation is where this bites first).

## 2. Install these three mods

| Mod | Nexus (Skyrim SE) | Exact file used |
|---|---|---|
| Complete Controller Setup 5.3.5 | [99978](https://www.nexusmods.com/skyrimspecialedition/mods/99978) | `1_Complete Controller Setup-99978-5-3-5-1747916448.zip` |
| Gamepad++ 1.2.1 | [27007](https://www.nexusmods.com/skyrimspecialedition/mods/27007) | `1_Gamepad Plus Plus-27007-1-2-1-1616967745.7z` |
| Auto Input Switch **1.1.2** | [54309](https://www.nexusmods.com/skyrimspecialedition/mods/54309) | `1_Auto Input Switch-54309-1-1-2-1630404989.zip` — under **Old Files** |

> **Auto Input Switch: do NOT use the current 1.2.3 main file.** It is an AE-only DLL (no
> `SKSEPlugin_Query` export) and silently fails to load on 1.5.97. Use **1.1.2 from Old Files**
> (the 2021-08-31 SE build, verified working on this list), or the 1.2.3-for-1.5.97 backport at
> [mod 166519](https://www.nexusmods.com/skyrimspecialedition/mods/166519).

CCS has a FOMOD layout choice; the reference install uses the default **Layout 133**. Enable both
plugins it adds: `CompleteControllerSetup.esl` and `Gamepad++.esp`.

**Requirements already in the list** (CCS hard-requires these; nothing to add): MCM Helper, True
Directional Movement, Wheeler, One Click Power Attack NG, TK Dodge RE, Classic Sprinting Redone
(SKSE64), Dual Wield Parrying SKSE, SkyUI (built into Enderal).

## 3. Install "Zenderal - Controller Tweaks"

Three third-party files need Enderal-specific edits. Since the source mods must stay pristine for
Wabbajack, the edits ship as a small standalone mod that **overrides those files by conflict**.

**You do not need to build it — install the archive:**

1. Download **`Zenderal - Controller Tweaks.7z`** from this repo's GitHub releases.
2. Install it in MO2 like any mod (Install Mod → pick the archive).
3. Sort it **above** *Complete Controller Setup* and *Dear Diary Dark Mode* (see §4).

It is built from `src/ControllerTweaks/` by `build/build.ps1` along with every other Zenderal
patch, so it version-controls and re-releases with the rest of the list. The rest of this section
documents **what is inside it and why** — read it when something upstream updates, not to
reproduce the mod by hand.

### What's in it

| Path | Forked from | Change |
|---|---|---|
| `Interface\Controls\PC\controlmap.txt` | Complete Controller Setup 5.3.5 | Quick Stats combo unbound |
| `Interface\skyui\config.txt` | Dear Diary Dark Mode (white text) | gamepad sort bindings moved |
| `Scripts\_00E_Game_SkillmenuSC.pex` | SureAI's Enderal script | B + D-pad-Up opens Hero Menu, B closes |

### File 1 — `Interface\Controls\PC\controlmap.txt`

Verbatim copy of Complete Controller Setup 5.3.5's controlmap with **one change**: the
*Quick Stats* gamepad combo (B + D-pad-Up) is unbound, because it opens Skyrim's vanilla
perk-starfield menu — a UI Enderal never uses.

```
before: Quick Stats		0x35				0xff	0x2000+0x0001		1	1	0	0x908
after:  Quick Stats		0x35				0xff	0xff         		1	1	0	0x908
```

Only the 4th (gamepad) column changes; keep the tabs and trailing columns exactly as they are.

### File 2 — `interface\skyui\config.txt`

SkyUI's gamepad sort bindings are **not in any MCM** — they live in this config file, and in
Zenderal the winning copy belongs to **Dear Diary Dark Mode (white text)** (it carries all of
Dear Diary's UI theming, so it is the copy to fork, not SkyUI's). With stock values, equipping
with RB or dropping with L3 also re-sorts the item list. Copy Dear Diary's file verbatim and
change three lines in the `[Input]` section:

```
controls.gamepad.switchTab = 271 ; BACK           (unchanged)
controls.gamepad.prevColumn = 274 -> 280          (LB -> LT)
controls.gamepad.nextColumn = 275 -> 281          (RB -> RT)
controls.gamepad.sortOrder  = 272 -> 273          (L3 -> R3)
```

Result: LT/RT switch the sort column, R3 toggles sort direction, and RB (equip) / L3 (drop) no
longer touch sorting. These are the values CCS itself intends (its shipped MCM defaults say
280/281/273/271) — they just have no working pipeline into SkyUI on this list.

### File 3 — `Scripts\_00E_Game_SkillmenuSC.pex` (+ `Scripts\Source\` .psc)

Gives the combo freed up in File 1 a job: **B + D-pad-Up opens Enderal's Hero Menu, and B closes
it.** This is a recompile of SureAI's own script, verbatim except for the lines below.

**Why it is done in Enderal's script and not in Gamepad++.** [verified in-game 2026-08-16, after
trying the Gamepad++ route first.] Gamepad++ *can* put the Hero Menu's "H" key on a combo, and in
gameplay that works. But **Gamepad++ goes inert the moment any menu is open**, so nothing it binds
can ever *close* the menu — only Esc on the keyboard did. Enderal's own script is registered for
keys the whole time (that is how Esc closes it), so putting the chord there fixes opening and
closing together. Two further reasons it is the better home: it needs **no MCM configuration**,
and it stores **nothing in the save** — Gamepad++'s bindings live in the save game and only reload
from its `.gppd` when you press Info → "Reset to Defaults", which is a terrible fit for a
distributed list.

Every added line is marked `; ZP`:

```papyrus
int ZP_iGamepadModifier = 277        ; SKSE gamepad keycode: B
int ZP_iGamepadOpenKey  = 266        ; D-pad Up
bool ZP_bGamepadModifierHeld         ; RegisterForKey cannot express a 2-button chord
Event OnKeyUp(...)                   ; releases the modifier
```

plus two `RegisterForKey` calls in `UpdateKeyRegistration()` and the chord added to the existing
`OnKeyDown` condition. **No Property was added, removed or renamed** — verified by diffing the
compiled `.pex` string tables against a build of the pristine script (added: `OnKeyUp`, the three
`ZP_` names, `fHoldTime`, one compiler temp; removed: nothing). That check matters because the
host plugin stores this script's property *values* in its VMAD and binds them by name.

Loose scripts beat the copy in `E - Misc.bsa`, so this wins with no extra step.

> **Do not also ship a Gamepad++ preset binding the same chord to "H".** Both would fire, and the
> emulated H would toggle the menu shut the instant the script opened it. An earlier version of
> this mod shipped such a preset; it has been removed.

> The `.pex` was built with the Enderal source tree **first** on the `-i` import path (see
> CLAUDE.md, "The import path is first-wins"). To rebuild after an Enderal update, re-apply the
> `; ZP` edits to the new `.psc` and recompile the same way.

> **Maintenance:** all three files are full-file forks living in `src/ControllerTweaks/`. If CCS,
> Dear Diary Dark Mode **or Enderal itself** updates, re-copy the new file there, re-apply the
> change, and rerun `build/build.ps1` — otherwise the tweak mod silently reverts that mod's other
> fixes. The `.pex` must be recompiled and re-committed whenever the `.psc` changes; CI cannot
> compile Papyrus, and the build fails on a *missing* `.pex` but cannot detect a *stale* one.

> **Credit:** `_00E_Game_SkillmenuSC` is SureAI's script, redistributed in modified form solely to
> add gamepad support. Credit them on the mod page.

## 4. Priority order

Only the file conflicts matter; MO2's conflict flags confirm each:

1. **Zenderal - Controller Tweaks** wins against *Complete Controller Setup* (controlmap.txt)
   and *Dear Diary Dark Mode* (config.txt).
2. **Complete Controller Setup** wins controlmap.txt against *Gamepad++* and *Modern Toggle
   Walk-Run Fix for Enderal SE* (both also ship one).
3. Load-order position of the two plugins doesn't matter.

Reference install, highest priority first:
Zenderal - Controller Tweaks → Complete Controller Setup → Gamepad++ → Auto Input Switch.

## 5. The INI change

In the profile's `EnderalPrefs.ini` (profile-local INIs are on, so this is the live file and
Wabbajack captures it), find `[MAIN]` and set:

```ini
[MAIN]
bGamepadEnable=1
```

The list currently ships `bGamepadEnable=0` in `[MAIN]` — change that line rather than adding a
second one. Do **not** put it in `[Controls]`; the engine only reads it from `[MAIN]` (verified
by A/B test). If BethINI Pie is run afterwards, re-check the value survived — BethINI has
previously relocated this key into sections the engine ignores.

## 6. Verify

- [ ] `skse64.log` shows `AutoInputSwitch.dll ... loaded correctly` — if it says
      `does not appear to be an SKSE plugin`, the AE build is installed.
- [ ] With the pad on before launch: menus navigate, the character moves, and pad and
      mouse/keyboard work interchangeably.
- [ ] Inventory: RB equips and L3 drops *without* re-sorting; LT/RT change the sort column; R3
      flips sort direction.
- [ ] **B + D-pad-Up opens Enderal's Hero Menu, and B closes it** — no MCM setup required, works
      on an existing save. The vanilla perk-starfield menu is gone; B + D-pad-Right/Left/Down
      still open inventory/magic/map, and H/Tab/Esc still work on the keyboard.
- [ ] A new game reaches and exits character creation with either input device.

If the pad seems dead, check Windows first: an XInput probe from PowerShell (poll
`XInputGetState` slot 0) separates a sleeping controller from a game-side problem in seconds.

## 7. Side note found during diagnosis

`ImprovedCameraSE.dll` currently reports itself incompatible in `skse64.log` — it's an AE build,
same disease as the stock Auto Input Switch. Unrelated to controller support, but the list is
running without Improved Camera and nothing warns about it; worth swapping for a 1.5.97 build in
the same update.
