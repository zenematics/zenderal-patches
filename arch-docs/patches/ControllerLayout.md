# ControllerLayout

- **Source:** `src/ControllerLayout/`
- **Ships:** `Zenderal - Controller Layout.esp` (ESL, masters only `Skyrim.esm`) + `ZEN_ControllerLayout.pex` + the loose config files in `src/ControllerLayout/files/`
- **FormID block:** `0x800` (`ZEN_ControllerLayoutQuest`)
- **Status:** v2 built 2026-11-01. v1 tested in game the same day: Hero Menu on double-tap Right, RT power attack, hold-A Quick Light and the D-pad stance holds all worked (Papyrus log shows `stances_script.SwitchStance()` firing). Double-tap Left did nothing (see below), so v2 fixes it. **v2 is not yet tested.**

## What it does

The whole controller layout, and the keyboard binds that share its files, in **one MO2 mod you
can turn on and off**. It must have the **highest priority of every input mod** (above
`Zenderal - Input Defaults`, `Complete Controller Setup`, `Gamepad++` and `Zenderal - Settings`).
The in-game cheat sheet is `src/ControllerLayout/readme - Zenderal - Controller Layout.txt`,
which ships in the archive.

Two halves:

1. **Loose files.** Copied from what won in the Ultra profile on 2026-11-01 (Input Defaults'
   files plus `Zenderal - Settings`' `MCM/Settings/keybinds.json`), with these changes:
   - `Stances.ini` `stance_mid_pad` 40 (`'`) → 43 (`\`).
   - `OCPA.ini` is **unchanged (259, Mouse 4)**. RT comes from Patch Collection's
     `ZenOCPASecondKey.dll` (`iKeycode=281`). v1 set OCPA to 281 as well, and the DLL logs
     `Second key is OCPA's own key - nothing to add, staying idle`. RT still worked, but the
     keyboard Mouse 4 power attack was lost. **Never set OCPA's key to the second key's key.**
   - Back / B + Back / B + Start = Tween / Favourites / Wait (curator's choice, 2026-11-01; CCS had
     Wait / Tween / Favourites). Tween and Wait are gamepad-remappable, so the game takes them from
     `ControlMap_Custom.txt`'s gamepad block (`TweenMenu 0x00000020`, `Wait 0x20000010`). Favourites
     is not remappable on a gamepad (7th column 0), so it lives only in `controlmap.txt`
     (`0x2000+0x0020`). Change both files together.
   - Gamepad++ preset: double-tap Left `L` → `K`, double-tap Right `K` → `H`, hold Right `'` → `\`,
     and labels filled in.
2. **`ZEN_ControllerLayout`** (a player-alias script) handles what other mods keep **in the save**:
   - **Gamepad++.** It writes `gpp_keyhandler`'s auto-properties directly: the action/combo
     keycodes, the multi-tap and long-press flags, and the five 16-slot action arrays. It then calls
     `RegisterKeys()`. These are exactly the fields the MCM's `loadPreset` fills
     (`gpp_mcm_gen.loadData`, `gpp_mcm_act.loadData`).
   - **Quick Light.** `aaaQLPlayerAliasScript.SetLightKey(37)` moves its key L → K, and Gamepad++'s
     double-tap Left sends K. Hold-Activate stays on.
   - **The Hero Menu.** The script registers for B (277). While `CustomMenu` is open, B calls
     `_00E_Game_SkillmenuSC.OnKeyDown(1)` on `Levelsystem 010AA2` alias 0, which is Enderal's own
     Esc close path. Enderal's handler closes only when its own `MenuOpen` flag is set, so B in any
     other custom menu does nothing there.

   The Gamepad++ and Quick Light writes run **once per save per `LAYOUT_VERSION`**, 15 s after
   init or load, with up to 8 retries while Gamepad++'s arrays are still `None`. Later MCM changes
   therefore stick. **Bump `LAYOUT_VERSION` to push a changed layout into existing saves.** Every
   target is found with `GetFormFromFile` and a cast, so a missing mod is skipped.

## Why each fix (diagnosis 2026-11-01)

- **Holding D-pad Right toggled the compass.** Gamepad++ sent `'` for the mid stance, and
  `'` (40) is also **No Compass In Dialogue's** `hcomControlScript.ToggleKey` default.
- **Double-tap Left ("lantern", L) was really Quick Light.** No lantern mod is installed:
  `keybinds.json`'s `SWLToggle`/`toggleLantern` entry is stale, and no enabled mod ships an
  `SWLToggle` MCM. On L it was Quick Light's `LightKey`, plus Enderal's horse key
  (`_00E_HorseFlute_SC.iMountHotkey`). v1 moved Quick Light to K and left the gesture on L, so it
  did nothing. v2 sends K. The horse stays on L because it is Enderal's default, and
  `SetMountTeleportKey` registers the key even before the player owns the flute.
- **No controller Hero Menu.** The B + D-pad Up fork of `_00E_Game_SkillmenuSC` no longer ships
  in any enabled mod, and Input Defaults' preset had changed CCS's double-tap Right `H` to an
  unused `K`. Gamepad++ cannot close the menu. It only sends keys, and Enderal's exit keys are
  only Tab and Esc, so the close needs its own listener.
- **Quick Light on hold A** is Quick Light's default (`UseHoldKey = true`). It is kept, because
  players reported it as a feature. CCS's `MCM/Settings/QuickLight.ini` cannot change it, since
  Quick Light uses a legacy SkyUI MCM and not MCM Helper.

## Gamepad++ data layout (from the decompiled 1.2.1 scripts)

- `aiNonComboActions[button * 4 + press]`. Buttons: 0 = A1 Left, 1 = A2 Right, 2 = A3 Up,
  3 = A4 Down. Presses: **0 = hold**, 1 = single, 2 = double, 3 = triple
  (`gpp_keyhandler.OnUpdate`: `i * 4 + iMultiTap`).
- A `.gppd` preset stores each button as **[single, double, triple, hold]** (KH indices 1, 2, 3, 0),
  each as an `[int, label]` pair. `General` holds `[A1..A4, C1..C4, 4th combo, ext controls,
  multi-tap, long-press]`.
- The key handler is alias **1** on `gpp_controlquest 000800:Gamepad++.esp`. Gamepad++ disables
  itself in the vanilla menus it registers for, but `CustomMenu` is not on that list.

## Stances: what reads the keys

The winning `DtryKeyUtil.dll` is PaulMix's rewrite, which does **not** read
`dtryKeyUtil/config/custom`. The stance keys are read by Patch Collection's **`ZenKeyTrace.dll`**,
which logs every binding to `My Games/Skyrim Special Edition/SKSE/ZenKeyTrace.log` (source on
`origin/feat/enderal-paired-anims`, `src/ZenKeyTrace/`). `stances_script` switches only with a
weapon drawn. Every switch logs `RemovePerk called with invalid Perk` (one stance has an empty
`remove` perk) and a `Dispel` error (ZenKeyTrace removes the ability on key-up first). Both come
from the Stances mod and are harmless.

## Swift Potion combos (v3)

Combo key 1 is A (CCS's choice). `aiC1Actions` single-press slots 1/5/9 (Left/Right/Up) send
203/205/200, which are Swift Potion Reborn's hotkeys as `Zenderal - Settings Applier`'s
`HotkeyData.json` writes them (← health, ↑ mana, → stamina). Swift Potion keeps hotkeys in the
save, so a player who rebinds them in its MCM breaks the match. `gpp_keyhandler.OnUpdate` reads
`bIsC1Held` when the multi-tap delay (0.3 s) ends, so A must still be held then. Quick Light's
hold-Activate (0.5 s, nothing targeted) shares A.

## Caveats

- Turning the mod off does **not** undo the save-stored writes. To undo them, use Gamepad++ MCM →
  Restore Default Settings.
- Quick Light's MCM still *shows* L: its label is a private variable.
- Every D-pad press also fires that button's favourites hotkey (5–8), including the first press of
  a double-tap or hold. This is CCS's design and is unchanged.
- If CCS, Input Defaults or a keybind mod changes upstream, re-copy the files and re-apply the
  three edits above. Otherwise this mod silently reverts the upstream fix.
