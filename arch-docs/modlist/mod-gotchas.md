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
  Single-key files keep keyboard: OCPA 259 (controller holds RT), BTPS Shift+wheel, SKSE Menu Framework F7 (pad
  toggle OFF — CCS's F1 collided with Stances). CCS's `BowRapidCombo.ini` / `Dynamic Activation Key - MCM.ini` /
  `QuickLight.ini` are inert here (no matching MCM config installed).

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
  `DynDOLOD.esp` + `Occlusion.esp` after `ReadTheRoom.esp`.

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
