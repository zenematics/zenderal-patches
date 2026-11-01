# ControllerLayout

- **Source:** `src/ControllerLayout/`
- **Ships:** `Zenderal - Controller Layout.esp` (ESL, masters only `Skyrim.esm`) + `ZEN_ControllerLayout.pex` + the loose config files in `src/ControllerLayout/files/`
- **FormID block:** `0x800` (`ZEN_ControllerLayoutQuest`)
- **Status:** built 2026-11-01, **not yet tested in game**

## What it does

The whole controller layout, and the keyboard binds that share its files, in **one MO2 mod you
can turn on and off**. It must have the **highest priority of every input mod** (above
`Zenderal - Input Defaults`, `Complete Controller Setup`, `Gamepad++` and `Zenderal - Settings`).
The in-game cheat sheet is `src/ControllerLayout/readme - Zenderal - Controller Layout.txt`,
which ships in the archive.

Two halves:

1. **Loose files.** Copied from what won in the Ultra profile on 2026-11-01 (Input Defaults'
   files plus `Zenderal - Settings`' `MCM/Settings/keybinds.json`), with three changes:
   - `Stances.ini` `stance_mid_pad` 40 (`'`) → 43 (`\`).
   - `OCPA.ini` `iKeycode` 259 (Mouse 4) → 281 (RT). CCS binds attacks to LB/RB, so RT does
     nothing else in gameplay (see `modlist/mod-gotchas.md`, 2026-10-17).
   - Gamepad++ preset: double-tap Right `K` → `H`, hold Right `'` → `\`, labels filled in.
2. **`ZEN_ControllerLayout`** (a player-alias script) handles what other mods keep **in the save**:
   - **Gamepad++.** It writes `gpp_keyhandler`'s auto-properties directly: the action/combo
     keycodes, the multi-tap and long-press flags, and the five 16-slot action arrays. It then calls
     `RegisterKeys()`. These are exactly the fields the MCM's `loadPreset` fills
     (`gpp_mcm_gen.loadData`, `gpp_mcm_act.loadData`).
   - **Quick Light.** `aaaQLPlayerAliasScript.SetLightKey(37)` moves its key L → K. Hold-Activate
     stays on.
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
- **Double-tap Left fired three mods on one key.** L is Simple Wearable Lantern's
  `toggleLantern`, Quick Light's `LightKey` and Enderal's horse key
  (`_00E_HorseFlute_SC.iMountHotkey`). Quick Light was moved off L. The horse stays on L because
  it is Enderal's default and `SetMountTeleportKey` registers the key even before the player owns
  the flute.
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

## Caveats

- Turning the mod off does **not** undo the save-stored writes. To undo them, use Gamepad++ MCM →
  Restore Default Settings.
- Quick Light's MCM still *shows* L: its label is a private variable.
- Every D-pad press also fires that button's favourites hotkey (5–8), including the first press of
  a double-tap or hold. This is CCS's design and is unchanged.
- If CCS, Input Defaults or a keybind mod changes upstream, re-copy the files and re-apply the
  three edits above. Otherwise this mod silently reverts the upstream fix.
