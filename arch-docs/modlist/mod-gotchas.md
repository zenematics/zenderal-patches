# Third-party mod gotchas

List-wide traps that are not tied to one Zenderal patch.

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **TK Dodge under Pandora: install TK Dodge RE's "TK dodge standalone" (`tkds`) FOMOD options, or
  every third-person dodge plays on the spot.** **[verified in game 2026-10-08]** TK Dodge RE's
  "Main files" option installs only the `tkuc` (Ultimate Combat) engine patch, which has no
  `animationdatasinglefile` part. Nemesis used to supply that data from its own bundled `tkuc`;
  Pandora 5.0.0-beta does not (its bundled `tkds` is first-person only and has no `info.ini`, so it
  is never applied), so the step-dodge clips had no motion data and the character shuddered in
  place. Fix: reinstall TK Dodge RE ticking every "Behavior edits for dodge only" box except the
  non-TDM "Allow dodging when stagger", then in Pandora tick **TK Dodge Standalone** and untick
  **TK Dodge RE / Ultimate Combat**. Pandora's author only supports TK motion via AMR annotations
  (Monitor221hz/Pandora-Behaviour-Engine-Plus#28), so the list also runs *TK Dodge Animation
  Pandora Patch* (AMR-annotated default clips) and *TK First Person Fix for Pandora*. **A FOMOD
  reinstall resets `TK Dodge RE.ini`** (dodge key fell back to Left Alt = Jump), so the list's dodge
  settings (Space 57, step dodge, stamina 5) now live in `Zenderal - Settings`. Diagnostic: grep the
  Pandora output's `animationdatasinglefile.txt` for `^TKDodge` - zero lines means no motion data.
- **Pandora 5.0.0-beta cannot build FNIS paired (`pa`) or killmove (`km`) animations, so Enderal's
  paired cinematics are dead under it.** **[verified from source + output 2026-10-16; in-game
  confirmation pending]** Pandora's FNIS support (`Pandora.Skyrim/Format/FNIS/`, tag `v5.0.0-beta`)
  only registers each listed clip in `DefaultMale/Female.hkx` and splices the mod's *shipped*
  `FNIS_<mod>_Behavior.hkx` into `0_master`'s root state machine; `BasicAnimation.BuildBehavior` is
  an empty stub and the `Paired` case in `FNISAnimationFactory.Create` is commented out. FNIS puts
  `pa`/`km` entries inside `0_master.hkx` itself, and Pandora's `0_Master.hkx` (rebuilt from its
  vanilla template) overrides Enderal's FNIS-built one. Affected — all six such lines in
  `fnis_enderal_list.txt` (shipped loose by *Enderal- Fores New Idles Patch - FNIS Patch*):
  `km CaliaMassacre` (IDLE `pa_MQ07b_CaliaMassacre 13FAA3`, MQ07b), `pa HugB` (`0F4699`) and the four
  `pa Kiss*` (`13FA92`, `13FA9C`, `13FA9D`, `141596`). Enderal's stock `0_master.hkx` contains
  `CaliaMassacre`; Pandora's contains none. Nothing is logged — the list "parses" fine. The 45
  `b`/`s`/`+`/`ch` lines ride Enderal's stock `FNIS_Enderal_Behavior.hkx` and may still work.
  **Fixed 2026-10-16, verified in game** by
  [`patches/EnderalPairedAnims.md`](../patches/EnderalPairedAnims.md): tick both *Zenderal - Enderal
  Paired Animations* entries in Pandora. Lesson: a paired/killmove clip needs **two** things — the
  graph states in `0_master` *and* the clip listed in `animationsetdatasinglefile.txt`; with only the
  first, the event fires, the clip fails to load (A-Pose Fix logs "Converted animation file") and both
  actors stand still.
- **Keybinds: the list default and the curator's personal layout are two MO2 mods.**
  `Zenderal - Settings` carries the default (`Root/ControlMap_Custom.txt`, Dual Wield Parrying's and
  Wheeler's configs); the optional `Zenderal - Personal Keybinds` overrides it when sorted above it
  and must be disabled before a Wabbajack compile. For USERS, the list ships a third, disabled MO2
  mod, `Custom Keybinds` (added 2026-10-09, directly below `Zenderal - Settings` in the left pane):
  the list's `TK Dodge RE.ini` and `DualWieldParryingSKSE.ini` verbatim plus an instructions header
  (free keys U/K/N, DWP mouse codes). Users edit it and tick it. **In MO2's left pane LOWER wins** —
  the "sort above" wording elsewhere in these docs is `modlist.txt` order, which MO2 writes reversed.
  `ControlMap_Custom.txt` is BINARY: 3 blocks
  (keyboard, mouse, gamepad), each a 3-byte header then 5-byte entries `u8 event, u32 BIG-ENDIAN
  key`, event = index in the live `controlmap.txt` Main Gameplay list (6 Left Attack, 7 Right
  Attack, 0x15 Favorites). Dual Wield Parrying numbers mouse buttons **+257**, not the CK's +256
  (right click 258, Mouse 5 261).
  **The game READS `ControlMap_Custom.txt` from `Data\`, not the game root.** **[verified in game 2026-10-10]**
  `SkyrimSE.exe` names it as a bare relative path next to `Interface/Controls/PC/ControlMap.txt`, and the
  engine's loader resolves those against `Data\` — but in-game remaps are WRITTEN to the game root, where Root
  Builder (copy mode) syncs them back over the winning mod's `Root\` copy on exit. Enabling **Complete Controller
  Setup** (which ships a loose, stock-keyboard `ControlMap_Custom.txt` in its mod root = `Data\`) silently replaced
  every keyboard bind; a file under `Root\` alone is never read. Fix: ship the map at the MOD ROOT of a mod that
  outranks CCS (`Zenderal - Personal Keybinds` now carries it in both places). Also keep each block's entry count
  = the live controlmap's remappable-flag count (header byte = `3 + 5×entries`; the controller controlmap makes
  Quick Stats keyboard-remappable, 26→27) and the gamepad block = that controlmap's defaults.
  **CCS also overrides five `Zenderal - Settings` files with controller-only values** — `MCM/Settings/OCPA.ini`
  (power attack 259→281 RT), `SKSE/Plugins/TK Dodge RE.ini` (Space hotkey disabled, sprint-tap dodge, stamina
  10), Wheeler `Controls.ini` (all keyboard binds zeroed), `DualWieldParryingSKSE.ini` (parry 261→280 LT) and
  `BetterThirdPersonSelection.ini` — because Settings sorts BELOW CCS. CCS ALSO replaces the Stances mod's
  `SKSE/Plugins/dtryKeyUtil/config/custom/Stances.ini` (stance keys F1–F4 → `[ ' ; ]`) and alone supplies
  `BowRapidCombo.ini` / `Dynamic Activation Key - MCM.ini` (both hotkeys → 281 RT) and a SkyUI MCM Helper
  `settings.ini` that beats MCM Helper's. Its `Stances - Dynamic Weapon Movesets SE.ini` is inert (no MCM config).
  Personal Keybinds now carries the five plus the stance file; Wheeler/BTPS there are merged (keyboard + CCS pad).
  OCPA and DWP take ONE key, so a keyboard and a controller default cannot coexist in one file. **Fixed
  2026-10-11 by the MO2 mod `Zenderal - Input Defaults`** (compiler Include + AlwaysEnabled; must sort ABOVE CCS
  and BELOW Personal Keybinds in priority): the list defaults from `Zenderal - Settings` / the original mods, with
  controller values merged wherever a file has room — `ControlMap_Custom.txt` at Data root (Settings' `Root\` map,
  already 27/25/12 against the controller controlmap), DWP `ParryKey2 = 280`, Wheeler gamepad section from CCS,
  Stances F1–F4 plus `[ ] ; '` under extra `*_pad` names (Gamepad++ D-pad long presses send those keys — the
  duplicate-name lines work — **verified in game 2026-10-11** along with the rest of the mod, Personal Keybinds off), SkyUI MCM column buttons 280/281/273, TK Dodge Space + `EnableSprintKeyDodge`.
  Single-key files keep keyboard: BTPS Shift+wheel, SKSE Menu Framework F7 (pad
  toggle OFF — CCS's F1 collided with Stances). CCS's `BowRapidCombo.ini` / `Dynamic Activation Key - MCM.ini` /
  `QuickLight.ini` are inert here (no matching MCM config installed).
  **OCPA is the exception: it takes the controller key, 281 RT** (changed 2026-10-17, from 259 Mouse 4). CCS's
  controlmap binds Left/Right Attack to **LB/RB** (`0x0100`/`0x0200`); **RT is unbound in gameplay**, so it
  attacks only through OCPA. With 259, holding RT did nothing. Keyboard still power attacks by holding left
  mouse (`iLongPressMode = 0`, vanilla). **[verified by the user 2026-10-17: hold RT did nothing, hold LMB worked]**
  - **A modlist reinstall on 2026-10-17 shipped Input Defaults' `TK Dodge RE.ini` with
  `EnableSprintKeyDodge = false` and `EnableDodgeAttackCancel = false`**, so tapping B never dodged (the TK Dodge
  log prints both values at load). Both were set back to `true` locally; fix the list's published copy, or the
  next reinstall reverts it again.
  - **`ControlMap_Custom.txt` overrides `controlmap.txt`, gamepad section included** — so a CCS update to
  `controlmap.txt` does nothing while Input Defaults' custom map carries the old gamepad block. Binary
  format (decoded by hand, header bytes not fully understood): the file opens `02 00 8a`, the gamepad section
  opens `02 00 3f` at `0x10A`;
  keyboard entries are `[uint32 LE event][scancode]`, gamepad entries `[event][uint16 BE modifier][uint16 BE
  key]` (e.g. `0a 20 00 00 20` = event `0x0a` Tween Menu on B `0x2000` + Back `0x0020`). Tween = event `0x0a`,
  Wait = `0x20`. **When CCS updates, copy its gamepad section (from `0x10A`) over ours byte for byte.** Done
  2026-10-20 for CCS's Tween/Wait swap (Tween = Back, Wait = B+Back) after the controlmap-only fix showed the
  old binds in game [reported by the user: View opened Wait, B+View opened Tween, fixed by disabling Input Defaults].

- **Loading screens showing an old screenshot of your character and an empty centre frame = po3's Photo
  Mode, not a renderer or UI mod.** **[verified in game 2026-10-11]** Photo Mode's `bLoadScreenPics`
  (default `1`) feeds every photo saved in Photo Mode (`overwrite/textures/photomode/screenshots/*.dds`)
  into loading screens (`[LoadScreen] iChanceFullScreenArt`/`iChancePainting`, 25 each), so Enderal's
  own art stops appearing. The list now ships `bLoadScreenPics = 0` in
  `Zenderal - Settings/MCM/Settings/PhotoMode.ini`. Theo's Render Pipeline was suspected first and
  was wrong.
- **Theo's Render Pipeline "could not start rendering … nvngx_dlssg.dll was not loaded from the
  configured Streamline directory. NVIDIA reported a DLSS Frame Generation override" = a GLOBAL DLSS
  override in the user's NVIDIA App.** **[verified by a user report 2026-10-12]** The user's own
  machine, not the list: the per-game Skyrim SE profile shows its DLSS overrides as **Unsupported**
  (greyed out), so the forcing setting is under **NVIDIA App → Graphics → Global Settings → DLSS
  Override** (Frame Generation / Model Presets); setting those back to the 3D application setting
  fixed it. A working log reads `Read SL_DLSS_OVERRIDE DRS key (app profile): 0` and
  `NGXSecureLoadFeature … dlssg snippet: …TheosRenderPipeline Standard 0.4.1…\Streamline/nvngx_dlssg.dll`
  — compare a failing user's log against those two lines before guessing further.
- **"Broken on one save only, fixed by loading another save first" = a stuck animation-graph variable stored IN THE SAVE.**
  **[verified 2026-10-11]** Joseph's shield dropped the moment he moved while blocking. Every mod toggle (OAR sets,
  Pandora runs without SCAR/TK, keybinds, Timed Block, Shield Runner respec) changed nothing, because the cause was
  save state. A save stores the player's whole Behavior graph (`BShkbAnimationGraph`: active state names, then every
  graph variable as `u16 len, name, u8 type(1 = 4 bytes, 0 = 16 bytes), value` up to `$-NoMoreVariables-$`) inside the
  player's ACHR change form (`000014`). A fresh boot rebuilds the graph from it, while a save-to-save load reuses the
  live graph — so the bug only shows on a direct boot. Diffing a broken and a working save of the SAME character, same
  gear, same pose (`src/SettingsApplier/tools/capture/graphdiff.py`) gave exactly one difference: vanilla 0_master's
  **`bAttached` = 1** (gates `currentDefaultState >= 10 && bAttached == 1` "attached" modes; set by a vanilla modifier
  list on attach/detach events — something attached the player and the detach never fired). Fix for the user: keep a
  save made after loading another save first (its `bAttached` is 0). Root trigger not yet identified.
- **A stale Cached Recursive Directory Walk (CRDW) cache makes newly installed files silently
  unloadable — rebuild it after EVERY install and every Pandora/Nemesis run.** **[verified in-game
  2026-10-07, after a full day of wrong diagnoses]** CRDW (Nexus 186434) caches the game's startup
  walk of `Data\Meshes`/`Textures`/… into `overwrite/SKSE/Plugins/data_*_.cache`. The list shipped it
  with `ShowPopUp=b:false` + `Mode=s:LOAD`, so the cache froze on 2026-10-05 and nothing installed
  after that could be loaded: SIGMA's 1st-person dagger clips showed `Activate [Replaced]` in the OAR
  log and then never played (arms vanish, no sound, no hit), while the SIGMA sword set (installed in
  August, inside the cache) worked. It looked like broken clips, a behaviour-engine bug and an A-Pose
  Fix bug in turn; a bisect from the full profile pinned it to CRDW alone. Now `ShowPopUp=b:true` —
  answer **Yes** whenever mods or behaviour output changed. **Before debugging any "installed but
  does nothing" asset, check `data_meshes_.cache`'s timestamp against the mod's install date.**

- **A big flat white/grey sheet hanging in a small worldspace is DynDOLOD's TERRAIN UNDERSIDE.** **[verified in-game 2026-10-06]** Ref `MQP03Temple_UNDERSIDE_DynDOLOD_NOLOD` (MSTT `MQP03Temple_UNDERSIDE_DynDOLOD_BASERECORD`, model `meshes/Terrain/MQP03Temple/MQP03Temple_Underside.nif`, both in `DynDOLOD.esp`) was seen floating over the intro beach's rocks. DynDOLOD generates an underside for every worldspace not in `TerrainUndersideIgnoreWorlds` (`Tools/DynDOLOD/Edit Scripts/DynDOLOD/DynDOLOD_SSE.ini`) — this run did `MQP03Temple`, `MQP01Home`, `MQ09Isle`, `MaxKingsPass` and `Vyn` (logs `Tools/DynDOLOD/Logs/LODGen_EnderalSE_*_TerrainUnderside_log.txt`). The `MQP03Temple` one was built from terrain data covering only cells `-2,-3..2,3` of a `-4,-6..6,8` worldspace at `QualityLOD16=10`, i.e. a coarse approximation of the beach terrain, and can sit above real ground in rocky gullies. The underside only exists to hide gaps under DISTANT terrain LOD, which a `SmallWorld` intro area hardly has. Fix at the next DynDOLOD run by adding the small worlds to `TerrainUndersideIgnoreWorlds`; do not patch `DynDOLOD.esp` refs from a plugin — DynDOLOD renumbers them every generation. **Applied 2026-10-06:** `MQP03Temple_Underside.nif` renamed `.mohidden` in `DynDOLOD_Output` (sheet confirmed gone in game), and the four small worlds added to the ignore list (backup `DynDOLOD_SSE.ini.bak-2026-10-06`), so the next DynDOLOD run will not regenerate it.

- **NPCs Use Potions strips every corpse** when re-enabled — see [`patches/NpcPotions.md`](../patches/NpcPotions.md).
