# SettingsApplier

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/SettingsApplier/`
- **Ships:** `Zenderal - Settings Applier.esp` + `ZEN_SettingsApplier.pex`
- **FormID block:** `0x800`

## What it does

**The list's save-based MCM settings.** File-based settings (MCM Helper `MCM/Settings/*.ini`, `keybinds.json`, SKSE plugin configs, `ControlMap_Custom.txt`, RaceMenu presets) ship as files in the curator's **`Zenderal - Settings`** MO2 mod (moved out of `overwrite` 2026-10-05 — Wabbajack does not reliably capture overwrite). Legacy SkyUI MCMs keep settings IN THE SAVE, so this ESL's StartGameEnabled+RunOnce quest re-applies them once per save, 30 s after load (legacy MCMs initialise a few seconds in and some reset their globals): 28 globals (FEC, Helmet Toggle 2, Dismembering Framework, EVG, NASC, Bow Charge Plus, IEA, Immersive Interactions, and Smart NPC Potions' use chance 10 / max potions 1 / drop chance 50, added 2026-10-07 from Save22 — its MCM is globals-only) + 4 auto-properties (QuickLoot IE `QLIE_ShowInCombat`, Dynamic Things `targetsEnabled`/`targetsMultiplier`, NASC `staminacostproperty`) + **Swift Potion Reborn's JContainers settings** (added 2026-10-08): its auto-use/hotkey data are JContainers objects, not globals, so the release ships the curator's MCM exports (`data/SwiftPotion/*.json` → `SKSE/Plugins/Zenderal Settings Applier/SwiftPotion/`) and the applier loads them exactly as the MCM's *Load Settings* buttons do (assign `PotionData`, unregister hotkeys 1–12, assign `HotkeyData`, `SetHotkey` each) on `_AP_MainQuest 0xD62`; skipped if `HotkeyData` is 0 (JContainers not working). JContainers documents no base for relative paths, so `FindFile` tries `Data/<path>` then `<path>` via `JContainers.fileExistsAtPath` — **verified in game 2026-10-08** (a new character got the arrow-key hotkeys; which of the two paths matched was not recorded). To re-capture: MCM → Swift Potion → Save Settings, then copy `JCUser/SwiftPotion/*.json` into `data/SwiftPotion/`. Each global is verified by `GetFormFromFile` + `PO3_SKSEFunctions.GetFormEditorID`; each property write goes through a cast, so a missing/changed mod is skipped, not written. **Values were captured by decoding the save itself** (`src/SettingsApplier/tools/capture/`: `ess.py` LZ4+save/Papyrus decoder — SE uses 32-bit string-table count AND 32-bit string indices, 64-bit VM handles; global values are in Global Data Table 1 type 3; `pex.py` reads script initial values; `bsa.py` reads SE BSAs) and diffing against shipped defaults. Excluded on purpose: auto-detected flags (`*_Nemesis*`, `TDM_TrueHUD`, `TrueHUD_SpecialResourceBars`, init markers), live state (`HT_HelmetState`, `DF_ModStatus_GV`), Obsidian Weathers' seasonal globals (script-driven), and anything file-based (SkyUI 3D item via MCM Helper's SkyUI config + Vel'dun's `SkyUI_SE.ini`; Ultimate Immersion Toggle; Easy Console Commands' hotkey in `keybinds.json`). Only AUTO PROPERTIES can be set from another script — private MCM variables cannot, which is why menus are reached through their globals/properties. Compile stubs for the target scripts live in `Scripts/stubs/` (compile-only, never shipped); this machine also needs the git-ignored `papyrus-source/vanilla-stubs/` (it has no real vanilla Scripts.zip) — `GlobalVariable` there gained the real `GetValue`/`SetValue` natives. Regenerate: update `data/settings.json` → `tools/01-generate-applier.py` → compile → commit the `.pex`. **Verified in game 2026-10-05** (the curator's Immersive Interactions "Waiting Animation: Disabled" took effect on a new character). Two caveats: (1) **a menu whose choice is ALSO kept in a private variable keeps DISPLAYING its default** — e.g. II's Waiting Animation shows "Sit Down" because its label comes from private `WaitIndex`, while the feature reads `AR_Wait`, which the applier sets; calling the menu's own `OnOptionMenuAccept` is NOT a safe workaround, because its branches compare option IDs that are all 0 until the page is first drawn, so it would hit the first option (Slow Alchemy); (2) the 30 s `RegisterForSingleUpdate` **pauses while any menu is open**, including character creation, so a save made right after chargen can predate the apply — decode the save with `tools/capture` before concluding a value "didn't transfer".

## Ally health bars default off (2026-10-20)

The plugin now overrides FS's `_00E_ActorHealthBarsEnabled 01598B` to **0** (masters FS + Update added).
It replaces *Remove Ally Hud Bars* (Enderal Nexus 639), a 0-byte `_00e_gui_actorhealthbar.pex` that
blanked the widget script. On 2.1 that blank both trips EnderalSE.dll's script-version check and stops
`_00E_EnderalMCM` from linking (its `ActorHealthBarWidget` property is typed `_00E_GUI_ActorHealthBar`),
which is the *"_00e_enderalmcm ... N/A"* popup. 2.1's widget skips `RegisterEvents()` when the global is
0, and Enderal's MCM has an "Actor Health Bars" toggle that still turns them back on. No other list
plugin overrides the global. Applies to new games; an existing save keeps its stored value.

## Kill moves default off (2026-10-20)

The plugin now also overrides `KillMoveConfig 049425` and `KillMove 100F19` (both `Skyrim.esm`, both
`GlobalShort`) to **0**, copied from base Enderal 2.1 with only `Data` changed. Enderal 2.1 added a *Kill
Moves* toggle to its own MCM (`_00E_EnderalMCM`). It stores the choice in `KillMoveConfig` (new in 2.1,
default 1) and copies it into the engine's `KillMove` global on every game load (`OnGameReload`). So a
`KillMove` of 0 set any other way, for example `set KillMove to 0` in the console, is reset to 1 at the
next load. That is how kill moves and kill cams came back after the 2.1 update. No other list plugin
overrides either global. Applies to new games; an existing save keeps its stored value, so use Enderal's
MCM → Kill Moves (the curator turned it off there on 2026-10-20). Built and round-trip clean;
**deploy pending** (the game was running), so it is unverified in game.
