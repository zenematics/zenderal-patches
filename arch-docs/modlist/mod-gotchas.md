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
  **Ship `ControlMap_Custom.txt` ONLY under `Root\`; any copy in `Data\` makes in-game rebinds reset every launch.**
  **[verified in game 2026-10-30]** `SkyrimSE.exe` loads the INI setting `sControlsRemapFile:Controls`
  (`ControlMap_Custom.txt`) through `BSResourceNiBinaryStream`, so a `Data\` copy wins; with none, it reads the
  game-root copy (Root Builder's). In-game remaps are WRITTEN by `BSWin32SaveDataSystemUtility` to the game root,
  and Root Builder (copy mode) syncs them back over the winning mod's `Root\` copy on exit. So while
  `Zenderal - Input Defaults` shipped the map in `Data\`, every rebind went to `Zenderal - Settings/Root` and the
  next launch loaded Input Defaults' unchanged copy again (player report 2026-10-30). Since 2026-10-30 the list
  default is `Zenderal - Settings/Root/ControlMap_Custom.txt` only; the `Data\` copies of Input Defaults,
  Personal Keybinds and **Complete Controller Setup** (a loose stock-keyboard map that silently replaced every
  keyboard bind when enabled, 2026-10-10) are `.mohidden`. Test: with only Root copies, Personal Keybinds'
  Favorites-on-G worked and Q (`controlmap.txt`) did nothing; a Toggle POV rebind survived quitting and relaunching.
  The game also re-saves the map unasked (same bindings, entries reordered), so a changed timestamp alone is not a rebind.
  A Wabbajack update restores `Zenderal - Settings/Root`, so players' rebinds reset on list updates. Also keep each block's entry count
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
  controller values merged wherever a file has room — `ControlMap_Custom.txt` (at Data root until 2026-10-30, now
  only in Settings' `Root\`; 27/25/12 against the controller controlmap), DWP `ParryKey2 = 280`, Wheeler gamepad section from CCS,
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
- **No longer applies: CRDW has been disabled since the 1.7.104 update (2026-10-21). Kept for the record.**
  **A stale Cached Recursive Directory Walk (CRDW) cache makes newly installed files silently
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

- **A big flat white/grey sheet hanging in a small worldspace is DynDOLOD's TERRAIN UNDERSIDE.** **[verified in-game 2026-10-06]** Ref `MQP03Temple_UNDERSIDE_DynDOLOD_NOLOD` (MSTT `MQP03Temple_UNDERSIDE_DynDOLOD_BASERECORD`, model `meshes/Terrain/MQP03Temple/MQP03Temple_Underside.nif`, both in `DynDOLOD.esp`) was seen floating over the intro beach's rocks. DynDOLOD generates an underside for every worldspace not in `TerrainUndersideIgnoreWorlds` (`Tools/DynDOLOD/Edit Scripts/DynDOLOD/DynDOLOD_SSE.ini`) — this run did `MQP03Temple`, `MQP01Home`, `MQ09Isle`, `MaxKingsPass` and `Vyn` (logs `Tools/DynDOLOD/Logs/LODGen_EnderalSE_*_TerrainUnderside_log.txt`). The `MQP03Temple` one was built from terrain data covering only cells `-2,-3..2,3` of a `-4,-6..6,8` worldspace at `QualityLOD16=10`, i.e. a coarse approximation of the beach terrain, and can sit above real ground in rocky gullies. The underside only exists to hide gaps under DISTANT terrain LOD, which a `SmallWorld` intro area hardly has. Fix at the next DynDOLOD run by adding the small worlds to `TerrainUndersideIgnoreWorlds`; do not patch `DynDOLOD.esp` refs from a plugin — DynDOLOD renumbers them every generation. **Applied 2026-10-06:** `MQP03Temple_Underside.nif` renamed `.mohidden` in `DynDOLOD_Output` (sheet confirmed gone in game), and the four small worlds added to the ignore list (backup `DynDOLOD_SSE.ini.bak-2026-10-06`), so the next DynDOLOD run will not regenerate it. **That edit went into the wrong file and the sheet came back with the 2026-10-15 rerun.** DynDOLOD in Enderal SE mode reads **`DynDOLOD_ENDERALSE.ini`**, not `DynDOLOD_SSE.ini` (`Logs/DynDOLOD_EnderalSE_log.txt` is the live log; the `_SSE_` log dates from August). **Fixed 2026-10-16:** the four small worlds plus `JaphetsFollyWorld` added to `TerrainUndersideIgnoreWorlds` in `DynDOLOD_ENDERALSE.ini` (backup in `E:\Zenderal-backups`), and the regenerated `MQP03Temple_Underside.nif` hidden again. After the next DynDOLOD run, confirm `LODGen_EnderalSE_MQP03Temple_TerrainUnderside_log.txt` is not refreshed.

- **Boot crash ~24 s in, `CommunityShaders.dll` `ShaderCache::GetCompletedShader` (`call [rax+0x08]` on a garbage
  pointer), compiling `RunGrass:Pixel` = Bottled Shaders' (CS 1.9) background shader compiler, not a plugin.** Seen
  2026-10-27 12:17 and 19:17, 10-28 14:40 and 22:14, 11-01 20:28 (Crash Logger, same function each time). It hits
  only while shaders compile: tonight's crash came during a rebuild of `overwrite/ShaderCache/DDC` (3,353 of 3,362
  files written 20:01-20:30), and the next launch went through. A use-after-free / race in the async compiler with
  `Zenderal - Settings`' 14 compiler + 8 background threads. Relaunching gets past it once the grass shaders are
  cached; if it repeats every launch, lower `Compiler Threads` / `Background Compiler Threads` (Advanced) or turn
  `Enable Async` off for one boot. Never blame a plugin enabled the same session (it happened before the
  RageEffectsRecolor and ramrod-prop plugins existed).

- **Random objects drawn flat white/grey (a sack, ground-cover plants, a different few each session) = Bottled
  Shaders' HiZ Occlusion Culling (v0.3.0, BETA). Off since 2026-10-30.** **[verified in game 2026-10-30]**
  The textures were loaded the whole time (`ZenTextureTrace` found nothing; the files, shader cache, VRAM and
  Theo's Neural Rendering were all ruled out first); turning the feature off in the Bottled Shaders menu fixed it.
  It defaults to on (`enableHiZCulling: true` in Bottled Shaders' defaults) and `Zenderal - Settings`' 
  `SKSE/Plugins/CommunityShaders/SettingsUser.json` had no `HiZ Occlusion Culling` section, so every player had it.
  That file now carries the section with `enableHiZCulling: false` (backup `E:/Zenderal-backups/2026-10-30-hiz-off/`).
  Recheck after a Bottled Shaders update before turning it back on. Found on the way: `SFO Complex Grass ENB`
  (complex-grass textures, colour in the top half and the normal map in the bottom, for ENB) under ordinary grass
  meshes that sample the whole texture; disabled in Ultra the same day, though it was not this bug.

- **NPCs Use Potions strips every corpse** when re-enabled — see [`patches/NpcPotions.md`](../patches/NpcPotions.md).

- **`Fix Lip Sync` (Nexus 75951) is a 32-bit Skyrim LE DLL** and never loads: `skse64.log` shows `couldn't load plugin LipSyncFix.dll (Error 193)`. Player lip sync under DBVO + CCC: see [`patches/DBVOPlayerLipSync.md`](../patches/DBVOPlayerLipSync.md).

- **`bGamepadEnable` is read from `[MAIN]` of `EnderalPrefs.ini`** (verified A/B in game 2026-08-16 — see [`zenderal-controller-setup.md`](../zenderal-controller-setup.md) §1/§5); `[Controls]`/`[General]` copies are ignored. On 2026-10-18 a `bGamepadEnable=1` was added under `[Controls]` of the Ultra profile on the mistaken belief that `[Controls]` is the live section — harmless, but it is not the setting. The 0.6.4 `.wabbajack` (compiled 2026-10-18 21:47) was checked by reading its `modlist` directives: it ships Ultra's `[MAIN] bGamepadEnable=1`, Complete Controller Setup, Gamepad++, Auto Input Switch 1.1.2 and Controller Tweaks enabled, and `Zenderal - Input Defaults`' controlmap/`ControlMap_Custom.txt` byte-identical to the live ones. To audit a compile the same way, open the `.wabbajack` as a zip, parse `modlist`, and read `InlineFile` entries by `SourceDataID`.

- **Testing the controller with `Zenderal - Personal Keybinds` enabled tests a layout players never get.** It sits above `Zenderal - Input Defaults` in Ultra and replaces OCPA (259 = Mouse 4, so **RT power attack does nothing**), DWP, Wheeler, Stances (F-keys only; dtryKeyUtil's log shows 4 keys, not 8) and TK Dodge with keyboard-only copies. The compiler Ignores it. (Found 2026-10-18.) **2026-10-19:** its controller-only values were synced to Input Defaults (SkyUI sort buttons 280/281/273, DWP `ParryKey2 = 280`, SKSE Menu Framework pad toggle OFF, Stances `*_pad` keys, Wheeler gamepad section), keyboard/mouse untouched; backup `E:\Zenderal-backups\2026-10-19-personal-keybinds-pre-controller\`. Still keyboard-only with it on, because each is ONE setting for both devices: OCPA (Mouse 4, so RT power attack stays dead) and TK Dodge (`EnableSprintKeyDodge = false`, so tapping B does not dodge; turning it on replaces Space dodge with sprint-tap). **2026-10-26:** TK Dodge turned on there too (`EnableSprintKeyDodge = true`, now the same settings as Input Defaults) so the controller dodges with Personal Keybinds on; backup `E:/Zenderal-backups/2026-10-26-tk-dodge-sprint/`.
- **LB alone draws/sheathes on 1.5.97 [reported in game 2026-10-18].** The CCS controlmap is an AE-era file (it has a `Creations Menu` context 1.5.97 lacks) and binds `Ready Weapon` = A+LB alongside `Left Attack/Block` = LB. On Enderal's engine LB alone fires Ready Weapon, so the A modifier is not honoured there. Unconfirmed but likely the same for every other gamepad combo: `Shout` A+RB, `Tween Menu` B+View, `Favorites` B+Menu, `Quick Inventory/Magic/Map` B+D-pad. Not a config value: the binding is CCS's as shipped (`ControlMap_Custom.txt` gamepad block byte-identical to CCS's). Only script/SKSE chords (like Controller Tweaks' B+D-pad-Up Hero Menu) are known to work.

- **Purple severed draugr/Lost One limbs and heads = `DF - Creatures by Xtudo - Draugrs` without Xtudo's draugr retexture. Disabled 2026-10-19 in Alpha 0.6 and Ultra.** **[verified on disk 2026-10-19; reported in game on Discord the same day]** Dismembering Framework maps every `DraugrRace` actor (Enderal's is `000D53:Skyrim.esm`, matched by EditorID) with ANY skin to the Official Creature Asset Pack's draugr limb meshes. Xtudo's DF pack (Nexus 126608, v1.3) sits above that pack in MO2 and replaces 44 of its 50 draugr meshes (limbs, heads and the gore-cap `dismembered_addons.nif`). It also replaces five vanilla draugr beard/helmet meshes. Its skin shapes point at `textures\actors\draugr\male\male1.dds`, `male2.dds`, `female\draugr1.dds` and `draugr2.dds` (+ `_n`). Those textures belong to Xtudo's "Draugrs - New models and textures", which the list doesn't ship, and no loose file or any of the 74 loaded BSAs has them, so every severed draugr limb rendered purple. The official pack's meshes use vanilla `textures\actors\draugr\draugr.dds` / `femaledraugr.dds` (in `Skyrim - Textures1.bsa`) and resolve. Xtudo's patch hub (SSE Nexus 123225) has nothing that fixes this: every file there needs that retexture too. Only re-enable the pack together with the retexture.

- **The Colossus boss was invisible because Mythical Giants Replacer for Enderal (Enderal Nexus 883) was installed without the original Skyrim mod's assets. Fixed 2026-10-21.** **[verified on disk 2026-10-21; reported in game the same day]** Its `MythicalGiantsReplacer.esp` is the winning `_70E_Boss_UniColossus 03D822`. It moves the boss to its own `GiantRaceIce 000901` with skin `000900`, whose ARMA (`DLC1_NakedFrostGiantAA 006DB9:Dawnguard.esm`, injected) uses `actors\MythicalGiants\frost\giant01.nif`. The Enderal mod ships only the `.esp`, so the boss had no body mesh. The original **Mythical Giants Replacer (SSE Nexus 147274, f1.00)** is now installed as the MO2 mod `Mythical Giants Replacer`, one line below the Enderal patch in Ultra, with **meshes and textures only**. Its archive also ships a Skyrim `MythicalGiantsReplacer.esp` with the **same filename** as the Enderal patch's plugin, so it was left out on purpose. If it is ever reinstalled from the full archive, the Enderal patch must keep higher MO2 priority or the Skyrim plugin replaces it. The frost mesh's `hsd_hair_normal.dds` ships in neither archive (a missing hair normal map, cosmetic only). The summonable Colossus `13DD46` is not touched (EGO's ebony giant).

- **NPCs Take Cover - Smarter Anti-Cheese AI (+ its Enderal patch) is disabled (2026-10-23, curator's decision).** Its
  SPID monitor spell sends every humanoid NPC to cover whenever the player attacks with a bow, crossbow/musket, staff or
  spell, or sneaks at them, so enemies broke off instead of fighting. The Lost One "fire once and flee" bug turned out to
  be separate (see [`patches/LostOneArcherAmmo.md`](../patches/LostOneArcherAmmo.md)), but the mod stays off.

- **Storms made the daylight sweep ("time passing quickly") = Bottled Shaders' Sky Sync, not the weathers (verified
  in game 2026-10-23).** Each lightning strike briefly re-aims the sun's directional light (vanilla behaviour, also
  the cause of the 2026-10-20 True Storms flicker). Sky Sync drives the light direction itself (`UseAlternateSunPath`
  true) and fades the shadow direction between sources over `ShadowTransitionDuration` 300 (~15 s at timescale 20),
  so every strike became a long shadow sweep. Did not happen under ENB. A/B test: `"SkySync": true` in
  *Zenderal - Settings*' `SKSE/Plugins/CommunityShaders/SettingsUser.json` → *Disable at Boot* stopped it
  (previous file in `E:/Zenderal-backups/2026-10-23-skysync-test/`). Turning lightning off in the weathers would only
  have hidden it. Don't toggle Sky Sync live under MO2 (shader recompile crash); use Disable at Boot.
  **Tuning does not fix it (tested in game 2026-10-23):** Sky Sync on with `ShadowTransitionDuration` 0 still swept, and so did `UseAlternateSunPath` false (transition back at 300). The sweep comes from Sky Sync's always-on job of deriving the light direction from the sun's sky position, which a strike moves; its other options only cover dawn/dusk/night. **Decision: Sky Sync stays off** (Disable at Boot). Re-enable only if Bottled Shaders fixes it (worth reporting: reproducible in any storm with lightning, unaffected by those two settings).
  **Superseded 2026-10-29:** the curator turned Sky Sync back on. A trace ([`patches/ZenSkySyncTrace.md`](../patches/ZenSkySyncTrace.md)) showed the explanation above was wrong: the sun never moves. The strike tilts the *directional light* to about 85° for the 0.5 s flash, and the sun shadows follow it up and down. [`patches/SkySyncLightningFix.md`](../patches/SkySyncLightningFix.md) holds the light on its pre-strike direction during flashes; verified in game 2026-10-29. **Sky Sync stays on.**

- **With Sky Sync on, rivers and waterfalls flickered at exactly 10 Hz = Bottled Shaders' *Throttle Water Reflection
  Cubemap* (fixed 2026-11-05, verified in game).** The curator's 120 fps capture (2026-10-30): the river's brightness
  jumped ~57 → 85 for 4 frames of every 12 while the rocks beside it held steady. Moving water reflects the water
  cubemap, and the throttle refreshes it at a reduced rate. Changing Sky Sync's sun position changed how strong the
  flicker was, which pointed at a reflection of the sun rather than at the water meshes. **Keep `"Throttle Water
  Cubemap": false`** in *Zenderal - Settings*' `SKSE/Plugins/CommunityShaders/SettingsUser.json` (menu: Advanced →
  *Throttle Water Reflection Cubemap*). Bottled Shaders' own `SettingsDefault.json` ships it `true`, so a reset of the
  user settings brings the flicker back. Cost not measured.

- **Enderal Retexture Project - PBR Conversion (Enderal Nexus 1063, "SPR PBR" 1.0.0) is installed without its landscape
  half (2026-10-24, curator's test).** Why: SRP's own `brickwall01` (Silvergrove/desert walls, `wall02.nif`) is SureAI's 2014
  art upscaled; SRP's mesh asks for a `_p` it never ships, so it parallaxed against our flat-grey filler and looked flat.
  Nexus had no modern replacement; this mod is SRP's same diffuse + normal with a height map and AI-made `_rmaos`
  (the author warns the roughness is weak). MO2 mod `SPR PBR - Architecture Dungeons Misc`, directly below
  *PBR and CM Landscapes of Vyn*: 903 files, `textures/PBR/enderal/*` + `PBRNifPatcher/enderal/*` only. **Left out:**
  `enderal/landscape`, `enderal/alternative`, `stonepath*`, `textures/PBR/landscape/*`, `PBRTextureSets/` and
  `SPR PBR.esp` (42 landscape TXSTs) — 258 of those paths are Piickl's newer, hand-made *Landscapes of Vyn*, which must
  keep them. No staged file overlaps any enabled mod (Vyn, TomatoRim, ERM CM/PBR checked). **Needs a PGPatcher
  rerun**; its 36 Ark wall-curb blocklist rules (see [`patches/ArkWallCurbFix.md`](../patches/ArkWallCurbFix.md))
  keep those meshes out. Modlist backup `E:/Zenderal-backups/2026-10-24-sprpbr/`. Unverified in game.

- **After a PGPatcher run, re-enable `TexGen_Output`, `DynDOLOD_Output` and `PG Patcher Output`, and their five plugins
  (found 2026-10-24).** TexGen and DynDOLOD output must be off while PGPatcher runs (curator's procedure; on that run
  `PG Patcher Output` was off too), and MO2 then drops `DynDOLOD.esm`, `PGPatcher.esp`,
  `PG_1.esp`, `DynDOLOD.esp` and `Occlusion.esp` from `plugins.txt`; turning the mods back on adds them **disabled, at
  the end**. `PBR Landscapes of Vyn.esp` masters `PGPatcher.esp`, and `Zenderal - Unresolved References Cleanup.esp`
  masters both PG plugins, so the game stops on missing masters without them. Positions: `DynDOLOD.esm` after
  `TrueHUD.esl`, `PGPatcher.esp` right after it, `PG_1.esp` after `Zenderal - Pretty Armory EGO Patch.esp`,
  `DynDOLOD.esp` + `Occlusion.esp` after `ReadTheRoom.esp`. **As of 2026-10-31** `ReadTheRoom.esp` is no longer in
  the profile; the tail is `… Zenderal - Unresolved References Cleanup.esp`, `DynDOLOD.esp`, `Occlusion.esp`,
  `Relentless Sword SE - Johnskyrim.esp`, **`Zenderal - Vyn Full Extend.esp` last** (it must follow `Occlusion.esp`;
  [`patches/UnifiedWaterEnderal.md`](../patches/UnifiedWaterEnderal.md)).

- **Grass LOD needs four things, and until 2026-10-31 the list had none of them** (no NGIO, no `Grass/*.cgid`
  cache, TexGen `GrassBillboards=0`, DynDOLOD `DoGrass=0`), so there was no distant grass at all. 41 of Enderal's 72
  GRAS also had no object bounds, which TexGen skips. Full setup and order: [`patches/GrassBounds.md`](../patches/GrassBounds.md).
  Traps: NGIO's `Only-load-from-cache = true` means **no grass at all until the cache mod exists**; `PrecacheGrass.txt`
  in the game root starts a cache run on **every** launch until a run finishes (NGIO 2.0.2 then deletes it; Root
  Builder excludes it, so it never cleans it up); a leftover progress `PrecacheGrass.txt` in `overwrite/Root/` resumes an old load order's run; TrueHUD crashes
  cache runs (use the `Grass Cache` profile). The tree-LOD brightness settings live in TexGen/DynDOLOD presets and
  `DynDOLOD_ENDERALSE.ini`, not in any mod (same doc).

- **The "black screen" after MQP01's Daddy scene is Enderal's intro video, by design (2026-10-25).**
  `_00E_MQP01_Functions.PlayIntroAndMovePlayerToShip()` plays `Video/EnderalIntro.bik` (Bink 1, 289 MB); it opens
  with a full sentence of narration over black before the picture starts. It is **interruptible**: a key press or the
  console during that black ends it at once and the game loads the ship (seen as ~30 s from Daddy's last line to
  MQP02's load). Chased through Theo's Render Pipeline, CS Upscaling and CS Effects11 (all A/B'd, all innocent)
  before the opening was recognised. A non-interruptible fork confirmed the video plays fine; the list now keeps all
  of Enderal's cinematics unskippable ([`patches/UnskippableCinematics.md`](../patches/UnskippableCinematics.md)).
  To skip videos on purpose: Enderal's MCM "Skip videos" (`_00E_VideoSkip 02E985:FS`).

- **Enemy poise bar colour lives in Chocolate Poise, not TrueHUD (2026-10-26).** Chocolate Poise - Reforged sends
  TrueHUD its own special-bar colour (`[TrueHUD] SpecialBarNormalColor` in `SKSE/Plugins/ChocolatePoise.ini`),
  which overrides Vel'dun's TrueHUD `sSpecialColor`. Shipped default was `FFFF00` (bright yellow). *Zenderal -
  Settings* now carries a full copy of that ini with only `SpecialBarNormalColor = B0A998` and
  `SpecialBarDepletedColor = 5D584E` (was `FFFFFF`) changed: Vel'dun's muted trim tone and dark trim edge, sampled from
  its UI frame (palette `CFC5AD`/`B0A998`/`8F8877`/`5D584E` on `211E1C`/`121212`; curator found its `sSpecialColor`
  gold `BF9766` too saturated); it beats Chocolate Poise by priority. **Re-copy from Chocolate Poise after it updates**
  (keep the one changed line), or the copy silently pins the old ini's other settings.
  The bar's refill flash is TrueHUD's own `sSpecialFlashColor`: set to `B8652A` (muted burnt orange, was Vel'dun's
  `FFA600`, which read as yellow) in the `Vel'dun Zenderal patches 16x9/21x9/32x9` and ultrawide `TrueHUD.ini`s
  (2026-10-26; backups `E:/Zenderal-backups/2026-10-26-veldun-flash/`).

- **H doesn't open the Hero Menu (fixed 2026-10-26).** In Enderal 2.1 the Hero Menu is opened by SureAI's
  `EnderalSE.dll` (`HeroMenuPatch`) from the game's **Quick Stats** control, not by a script; `_00E_HeroMenuAlias`
  says "unused, hero menu handling has been moved to DLL in 2.1+". Enderal's own controlmap (`E - Misc.bsa`)
  binds Quick Stats to `0x23` (H). The controller-setup controlmaps (CCS and our forks of it) carry Skyrim's
  `0x35` (`/`), and every `ControlMap_Custom.txt` in the list had Quick Stats **unbound** (`0xff`, event index 41
  in the keyboard block), so no key opened it. Quick Stats is now H in all four maps:
  `Zenderal - Personal Keybinds` (plus `Root/`), `Zenderal - Input Defaults`, and `Zenderal - Settings/Root/`.
  Each file was re-sorted by key and decodes cleanly. Backups are in
  `E:/Zenderal-backups/2026-10-26-controlmap-pre-quickstats-h/`. Hero Menu Enhanced is disabled in the list,
  and its `EnderalHeroMenu.dll` is the 2.0 route anyway (its script unregisters H). **Verified in game 2026-10-26: H opens the Hero Menu.**

- **Resolution and HUD layout are automatic (2026-10-26).** [`AspectLayout`](../patches/AspectLayout.md)'s
  `_ZenAspectLayout.dll` writes `SSEDisplayTweaks_custom.ini` with the primary monitor's resolution at every launch and
  copies Vel'dun's 16x9/21x9/32x9 HUD layout into place when the screen shape changes. Keep the 8
  `Zenderal - Resolution …` presets and the 3 `Vel'dun Zenderal patches` mods **disabled**: a preset's custom ini is
  overwritten each launch, and an enabled aspect patch is outranked (or, sorted above Aspect Layout, wins and pins its
  layout). Rerun `src/AspectLayout/tools/01` after a Vel'dun patch update.
- **Unified Water (Bottled Shaders) removed Vyn's distant water: its Vyn cache was missing (2026-10-28, verified in the
  log).** Turning the feature on replaces LOD water with its own, built from per-worldspace caches in
  `overwrite/SKSE/Plugins/CommunityShaders/UnifiedWaterCache/`. That folder held 17 caches but no `Vyn_cache.wc`, so
  the log said `Could not locate disk cache for Vyn`, then `No instructions found for Vyn chunk …` for every distant
  cell, and the sea beyond loaded cells was blank. Bottled ships a precache only for `Tamriel`; every other worldspace
  is built at runtime (Vyn takes ~1 s, the rest milliseconds), so the earlier build most likely ended before Vyn's
  finished (not proven; that run's log was overwritten). **Fix: Bottled Shaders menu → Unified Water → Debug →
  Regenerate Caches**, then check `BottledShaders.log` for `Vyn: Cache generated` and `18 / 18 complete`. Logs are now
  `SKSE/BottledShaders.log`; `CommunityShaders.log` is stale.
- **Break Stagger is off for NPCs (2026-10-31, curator's decision).** Break Stagger 1.0.2 (Nexus 178745,
  [source](https://github.com/vinymayan/Break-Stagger)) ran on its built-in defaults (no settings file anywhere): on
  every NPC `staggerStart` it counted the actor's staggers (count reset after 5 s) and sent `staggerStop`
  `2000 − 350 × (count − 1)` ms later (`src/Events.cpp` `HandleStaggerStart`): 2.00 s, 1.65, 1.30, 0.95, 0.60, 0.25,
  then 0 s + 3 s immunity at the 7th. That also cut FHR's parry knockdown (a 2.17 s stagger replacement), so
  enemies "got up in a split second". `Zenderal - Settings` now ships `Viny Mods/Break Stagger/Settings.json` =
  `{"player": {"enabled": true}, "npc": {"enabled": false}}` (the loader reads only the keys present; a disabled
  profile returns before counting). The player keeps the default anti-stun-lock. Its in-game page (SKSE Menu
  Framework) saves into that same file through MO2. FHR already rations NPC knockdowns with its own 10 s cooldowns.
  See [`FHRFirstPerson`](../patches/FHRFirstPerson.md). Unverified in game.

- **MCM Helper - Enderal Patch re-applies Enderal's MCM on every load** (2026-11-01): its `_00E_EnderalMCM` reads
  MCM Helper's ini in `OnGameReload`, so any plugin default or applier value for kill moves or the companion
  panel loses to its config default (both `1`). List defaults for Enderal's MCM go in `Zenderal - Settings`'
  `MCM/Settings/Enderal - Forgotten Stories.ini`. Details in [`SettingsApplier`](../patches/SettingsApplier.md).
- **Vel'dun UI 1.7's "Oblivion Icons patch 3 beta" fontconfig drops the `$Mage` font** (2026-11-05, Vini: three
  boxes above "Tier I" on Enderal talent cards). Vel'dun's item card (`skyui/itemcard.swf`, all variants) draws a
  talent's word, e.g. Steel Tempest's "Klo", in `<font face="$Mage">`, not `$DragonFont`. Vel'dun's own fontconfig
  loads `Interface\Mage.swf` and maps `$Mage` = `Mage`; the patch-3-beta fontconfig (the winning one, from
  `Veldun fomod files`, priority above `Vel'dun UI Enderal Default`) has neither, so every letter is a box.
  Fixed by adding those two lines to `Veldun fomod files/Interface/fontconfig.txt` (original in
  `E:/Zenderal-backups/2026-11-05-veldun-mage-font/`). **Re-add them after any Vel'dun reinstall or update**, or
  until upstream restores them. `fontconfig_ru.txt` never mapped `$Mage` and is left as Vel'dun ships it.
  Since 2026-11-09 the winning fontconfig is [`VeldunFuturaFont`](../patches/VeldunFuturaFont.md)'s, which
  carries the `$Mage` lines too.
- **The same patch-3-beta fontconfig moves the whole UI from Futura to Lato** (2026-11-09, curator): it maps all
  five menu fonts to `"lato"`; Vel'dun's own config maps them to `"Futura Book BT"`. Fixed by the override mod
  `Zenderal - Vel'dun Futura Font` ([`VeldunFuturaFont`](../patches/VeldunFuturaFont.md)), which must outrank
  every mod shipping `Interface/fontconfig.txt`.
- **Dismembering Framework never strips armour; a corpse that loses its clothes was stripped by a script**
  (2026-11-06, curator: Fog Wood bandits lost their clothing/armour "when dismembered"). Checked against DF 1.2.3's
  source (`Seb263/SkyrimSE_DismemberingFramework`, commit `eacedd8` = the shipped build), its JSON and the records:
  - **No cut variant → a generic limb, never a hidden piece.** `Main.cpp` `ProcessDismemberment` walks the node's
    DATA entries by `Priority` and takes the first whose `Conditions` pass. The humanoid pack's
    `OfficialHumanoidPack_Skyrim_DATA.json` matches vanilla armours by `IsEquipped` at −50; an Enderal armour matches
    none, so `OfficialHumanoidPack_DEFAULT_DATA.json` decides: `IsEquippedItemWeightClass` Heavy → the Iron limb,
    Light → Stormcloaks (forearm) / Hide (calf), Clothing → DefaultClothing (all −90), else the Naked limb (−100).
    The worn piece is left alone: the only code that touches it is `DropTargetItem`, gated on the LIMBS/TEMPLATES
    key `DropItem` (`"All"` / `"Armor"`, undocumented), and **no `_LIMBS`/`_TEMPLATES` file in the list sets it**
    (grep of `E:/Zenderal/mods`). `BipedSlot` (33 forearm, 37 calf) only picks which worn armour the weight-class and
    keyword conditions, `DropItem` and the heavy-armour cut sound look at (`GetWornArmor`); it hides nothing. The cut
    itself scales the limb bone to −0.01 (`ToggleNode`), which collapses every mesh skinned to it, armour included.
    **[verified in source]**
  - **What DF does equip: the stump cap.** `EquipArmorAddon` adds and equips the template's `ActorArmorAddon`, in the
    humanoid pack `DF_Humanoid_Naked_*_AR` `0x804/0x806/0x808/0x80A` — Clothing, NonPlayable, on biped slots **54 (L
    calf), 53 (R calf), 58 (L forearm), 59 (R forearm)**, ARMA priority 10 (`reference/mods/DFOfficialHumanoidPack`).
    Enderal's cuirass ARMAs are Body/Forearms/Amulet/Calves like vanilla's, so no overlap, but **five Enderal ARMAs
    do sit on a stump slot**: `02E_10_FineSteelBootsAA 0E4AD9` (53; Fine Steel Boots `02AE7D`, in the bandit outfit
    `00E_FeinstahlWithoutHelmet 0EAC1D`), `SheogorathBootsAA 0C7CBC` (53), `_00E_LeatherArmor_Cuirass_Var02_AA 14159F`
    (59; Leather Cuirass `01CBFC` + Forged), `_05E_40_Unique_MoralasBlessingAA 150375` (53) and FS's
    `_00E_FS_MQ18c_JesparBootsAA 01BEB1` (53). On the matching cut the engine must pick one of two priority-10 addons
    for that slot; which one shows is **[unverified in game]**. One ARMO carries a stump slot: the Father's
    `_00E_Father_BurntSkin 03834F` (Body/Hands/Feet + 59), so a right-forearm cut on him equips an ARMO on his own
    slot and unequips the burnt skin — the ordinary equip-slot rule, the one case where DF really does take armour off. The DF log's `The form obtained from the "IsEquipped"
    condition parameters is not valid` lines (10 per cut) are the Skyrim-only armour FormIDs in the Skyrim DATA that
    Enderal lacks (`Skyrim.esm:0x59E73` dragonscale etc., warned at load); harmless.
  - **The Fog Wood case is the arena's own strip.** `ZFW_ArenaQuest.GiveDrops` calls `akCorpse.RemoveAllItems()` on
    every dead spawn within a second of its death (`ProcessDeaths`, 1 s update), and `RemoveAllItems` on an actor
    removes worn items too — SureAI's own scripts re-dress right after it (`_00E_MQ05_Functions` prisoner rags,
    `_00E_FS_MQ18c_Functions` `akCompanion.RemoveAllItems()`). The waves before 2026-11-06 were creatures, so the
    strip showed for the first time with the bandit theme, the same day as the report. Whether a non-dismembered
    corpse shows the strip at once or only after DF's stump equip rebuilds its 3D is **[unverified in game]**; either
    way the fix is in the arena script (block the corpse's activation, or remove only unworn items), not in DF, and
    there is no DF setting, JSON key or keyword that would keep armour on a cut actor — it already does. **Applied
    the same day:** `GiveDrops` now calls `akCorpse.BlockActivation(True)` (no corpse menu, so still no loot), the
    `.pex` recompiled and deployed to MO2 mod `Zenderal - Fog Wood` at 14:42; unverified in game.
    See [`FogWood`](../patches/FogWood.md). **Rule: a corpse that loses its gear was stripped by a script — grep the
    list's `.psc` for `RemoveAllItems`/`UnequipAll` before blaming the dismemberment.**
- **Half Races Armor Patch for Enderal Steam Version (`EnderalHalfRacesArmorBugFix.esp`) removed from the list**
  (2026-11-06): it loaded at 459 and overrode, with 2.0-era copies, the Rat Catcher boots addon
  `_15E_HSet_BonejudgeBootsAA 0BEB5F` and Jespar's boots addon `1448D9` (identical to base 2.1), plus the old half
  races `033898`/`033899`, which [`EGO21Compat`](../patches/EGO21Compat.md) owns. On `0BEB5F` it dropped Pretty Unique
  Sets' **Calves** slot. Pretty's boot mesh keeps the mid-calf shaft in an `SBP_38_CALVES` partition, and **a mesh
  partition draws only when its own addon claims that slot**, so the boots showed as ankle shoes. Verified in game:
  with the mod removed, the boots reach mid-calf. A test patch that instead removed Calves from the cuirass addon
  `0BEB5B` hid the cuirass's own lower leggings (bare shins). That disproved the opposite rule ("another item's slot
  claim hides your partition"). The mod is redundant on 2.1, whose playable half races are `013746`/`013748`.
  **Rule: when an armor piece draws only partly, compare each partition's slot with the addon's `FirstPersonFlags`, and
  check which plugin last overrode that addon.**
- **CINEMACAM 2.0.1 changes the FOV around sprinting, in first person too.** Its Camera Noise sections carry *Sprint
  Effects*: `SprintZoomEnabled` / `SprintZoom=5` (a 5-degree FOV kick when a sprint starts, 0.15 s in, 0.35 s back) and
  `IdleZoomEnabled` / `IdleZoom=3` (a 3-degree zoom-in when a sprint stops straight to standing), each in
  `[NoiseThirdPerson]` and `[NoiseFirstPerson]`, on by default; with SmoothCam loaded CINEMACAM leaves camera positions
  to SmoothCam but its FOV effects still apply (its own strings say so). Its settings file is runtime-written
  `Data/SKSE/Plugins/Cinemacam.ini` - on the curator's PC that is MO2's `overwrite/`, the list ships none, so players
  get the plugin's defaults. 2026-11-09: the curator noticed the sprint FOV change in first person once Improved
  Camera stopped rewriting the camera FOV every frame (ZenICSheatheFix 1.5.4 `CameraFOV=0`); all four zooms turned
  off in that ini (`SprintZoomEnabled=0`, `IdleZoomEnabled=0` in both `[NoiseFirstPerson]` and `[NoiseThirdPerson]`,
  the curator's choice for both views); the sprint camera-noise rotation stays. **Shipped since 2026-11-09:** the
  ini was moved out of `overwrite/` into `Zenderal - Settings/SKSE/Plugins/` (the whole mod is Wabbajack-included), so
  players get it and CINEMACAM's in-game saves now land there through MO2's VFS, like IC's Zen.json. `[Camera] CustomFov=0` there, so CINEMACAM's own 85/85 FOV values are not applied.

- **Improved Camera 2.0 is body-only (2026-11-08, curator's decision).** IC SE 2.0.0.2226 keeps its settings in
  JSON profiles, not the 1.x ini: `mods/ImprovedCameraSE/SKSE/Plugins/ImprovedCameraSE/ImprovedCameraSE.json` names
  the active profile (`"active": "Zen"`) and the live profile is
  **`Zenderal - Settings/SKSE/Plugins/ImprovedCameraSE/Profiles/Zen.json`** (the IC mod itself ships only
  `Default.json`). The `Zenderal.ini` beside it is a dead IC 1.x profile: 2.0's DLL reads only `Profiles\*.json`
  (its strings checked). Zen.json was IC's defaults plus FOV 100 in every state; on 2026-11-08 it lost every feature
  but the body: camera transitions, free look (the head twisted up to 80° before the body shuffled round), yaw
  smoothing, directional sway and the walk/run/sprint sway intensities and the extra tfc controls (free camera).
  Camera transitions and Stabilization were tried ON again the same evening (with them off a chair's head camera
  copies the sit idle's head motion, does not follow the body's turn, and a bite cuts to the head anchor), and
  **reverted within the hour**: the curator rejects both as "IC doing more than the body". Open conflict. Kept:
  body + vanilla first-person arms (the list's 1P animation work — SIGMA, FHR First Person, musket ADS, pistol
  reload — needs them), head hidden, near-distance/anchor/restrict-angle body mechanics, bow/quiver/2H hidden on the
  back; dialogue camera, idle camera, letterbox and zoom were already off. **IC always applies its FOV table (2.0 has no master switch) - third person included:**
  `CAMERA::Manager::UpdateFOV` lerps the camera FOV to the profile's value every frame in every IC camera state
  but Free and Cinematic, so SmoothCam's per-state FOV offsets never showed (traced 2026-11-08: third person sat
  at 90-94 and flickered; the Apostate preset wants 69). ZenICSheatheFix 1.2.0
  ([`ImprovedCameraSheatheFix`](../patches/ImprovedCameraSheatheFix.md)) makes IC's ThirdPerson state hands-off
  (`[ImprovedCamera2] HandsOffFOVStates`; more states can be listed without a rebuild). The profile's 20 FOV
  entries are 94 = the list's `Enderal.ini` (`fDefaultWorldFOV`/`fDefault1stPersonFOV`); they were 100 until
  2026-11-08. **First Person FOV and Tween Menu Fix SKSE sorts ABOVE `Zenderal - Settings` in MO2** (modlist.txt
  line 55 vs 57), so its own ini (100/100 + a third-person override at 90) won and Settings' 94/94 copy was dead
  - which is why eating and cutscene chairs (IC's Animation/Furniture states at 94) zoomed in from 100.
  Settings' copy now also turns the third-person override off; the mod was moved directly below Settings in `modlist.txt` on 2026-11-08 21:08
  (MO2 closed; backup in `E:/Zenderal-backups/ultra-profile-20261108-210803-fov-mod-order`) and Settings' copy
  now says 100/100 = IC's Zen profile (the curator's choice). Keep IC's table and Settings' `FirstPersonFOV.ini`
  at one value, or the two fight every frame in first person. Saving from IC's in-game menu writes Zen.json back into Zenderal - Settings through the VFS. The
  profile is verified loaded; the FOV patch and the ini fix are unverified in game. **IC 2.0 also forces first
  person in its Animation camera state** (sitting, sleeping, bathing, fishing, boat/cart rides, scripted idles:
  each of its camera states asks for "third-person body" through a Modifier byte (`manager+0x30`) that SetMode
  honours by taking the third-person camera and zooming it onto the head - mode 2, no profile switch; found with a
  hardware write watch after three byte patches on the wrong path), which is why Immersive Interactions' *Force 3rd
  Person* did nothing and a chair looked first person. ZenICSheatheFix 1.5.x `ThirdPersonBody=0` NOPs the
  Furniture/Animation entry zoom + force sites (the head camera needs that zoom), so a chair, a bed, a mount are the
  vanilla / SmoothCam camera (verified in game 2026-11-08). The FOV drop on a chair or a bite (100 -> 91-95) was IC's
  first-person-state FOV store writing its lagging lerp every frame, hidden by the First Person FOV mod until the
  frame the camera leaves first person (camera-FOV write watch, 1.5.3); 1.5.4 `CameraFOV=0` NOPs both of IC's
  camera-FOV stores, so IC never writes the camera FOV and its FOV sliders are inert. Under that, the base FOV
  outside first person was the **save game's** (90, the FOV mod's old override): the engine saves
  `PlayerCamera::worldFOV`, so Settings' `FirstPersonFOV.ini` keeps the third-person override ON at 100 - one base
  everywhere, written every frame (SmoothCam offsets the frustum on top, it never writes worldFOV). Last piece:
  SmoothCam's standing `fovOffset -15` applies to the ThirdPersonState IC's head camera rides, which from the
  eyes reads as a zoom - 1.5.5 holds SmoothCam's camera control (its API) exactly while IC's mode is 2 (1.5.6: also
  while IC's pending flag is up, one frame earlier). **Verified in game 2026-11-08 22:14:** a bench is the vanilla
  furniture camera at a constant FOV 100; a bite is IC's head camera at FOV 100 for the whole animation. The
  curator then switched chairs to the head camera as well (`ThirdPersonBody=1`, 1.5.7, the hold also starting on
  the actor's sit/sleep state; **verified 22:23: chair = head camera at FOV 100 from the first frame**) - `=0` is
  the vanilla furniture camera. 1.5.8 tried the hold in a `PlayerCamera::Update` vtable hook: **the game never calls
  that slot** (the hold never fired, SmoothCam's offset was back) - 1.5.9 is back on `PlayerCharacter::Update`,
  which runs after the camera update; 1.6.0 also decides it in the late-frame `HUDMenu::AdvanceMovie` tick, which
  the traces show already sees IC's pending flag a frame before IC's camera update: **verified 22:48, the bite's
  first-frame offset is gone.** Final choice that night: **vanilla chairs** (`ThirdPersonBody=0`), head camera for
  scripted animations only. The bite's "height cut" measured with `[campos]` is (a) ONE frame of the vanilla
  third-person camera from behind the player (IC enters its ThirdPersonState in that frame but writes its position
  from the next) and (b) a steady ~10-unit forward jump: IC's head camera = `SmoothHeadAnchor(head) + (forward + 8)
  × bodyForward + right × bodyRight + (up + 1) × bodyUp`, the offsets being the profile's `Camera/Firstperson`
  (`ThirdPersonState::OnUpdate` → Modifier → `Manager::BasePosition`; they reach IC's own first person only in
  head-bob mode 1). Zen.json `Camera/Firstperson/forward = -10` (main + Combat) since 2026-11-08 night, and
  ZenICSheatheFix **1.7.0** `HoldCameraOnHeadCameraEntry=1` keeps the previous frame's camera-root transform on
  that one frame. **Both verified in game 23:21 (5 bites): the held frame logs once per bite and sits at the
  first-person position; the head camera then starts within 1.7 units of it.** Still there: the END of a bite cuts
  4-11 units back (the head leans forward at the animation's end; only an exit blend could hide it, not built), and
  bite 2 fell to IC mode 3 (plain third-person camera, SmoothCam's offset back) for 0.6 s mid-animation with the
  body request still up - SetMode's zoom check is the only path to that, a wheel tick the suspect, cause open.
  `Body/Action/*` offsets are body-vs-camera offsets, not the camera's. **1.8.0 (2026-11-09)**: in the head camera
  IC's `UpdateNearDistance` runs its first-person pitch rule (near plane 15 looking level, 4 at 50 deg down), and
  the mouth is ~10 units ahead of the camera, so a bite's food and hand were sliced by the near plane (recording);
  `HeadCameraNearDistance=4` caps the plane while IC's mode is 2, plain first person untouched. Verified 2026-11-09. A *scripted* forced third person (Eating Animations and
  Sounds always does one when you eat in first person; Immersive Interactions on *Force 3rd Person*) is a separate
  path (IC's Papyrus-side hook + a pending flag) and keeps IC's head camera by default (1.5.1), because the
  first-person arms have no eating/idle animations; `TakeOverForcedThirdPerson=0` + `IgnorePendingThirdPerson=1`
  make those a real third person instead. The zoom inside that head camera is the First Person FOV mod's
  third-person override (camera is technically kThirdPerson) - off in Settings' ini once that mod sorts below
  Settings. No Furniture Camera (modlist line 128) did not keep the furniture camera first person in the traces.
