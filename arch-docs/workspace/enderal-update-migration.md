# Enderal update migration — 2.0.12.4 / SSE 1.5.97 → 2.1.4.4 / SSE 1.7.104

The plan for moving the whole Zenderal list onto the new Enderal SE runtime. It covers the game, SKSE,
every SKSE DLL in the list (swapped to its AE build), our own patches, and regenerated outputs.

- **Today:** Enderal SE **2.0.12.4** on SSE **1.5.97** (`Stock game/Data/SKSE/Plugins/EnderalVersion.ini`). **[verified]**
- **Target:** Enderal SE **2.1.4.4**. The mod.pub changelog says 2.1.4.3 "Added compatibility with Skyrim
  SE 1.7.104" and 2.1.4.4 fixes issues on SSE 1.7 and 1.6.1179+. On Steam, expect **1.7.104**; GOG may be
  1.6.1179. **[upstream]** Confirm the real `SkyrimSE.exe` version in Phase 1 before swapping any mod.
- **Reported, not verified:** the 2.0 → 2.1 move needs a **new game** and uses a separate `EnderalSaves`
  folder.
- **Per-mod data:** [`enderal-update-dll-inventory.csv`](enderal-update-dll-inventory.csv). It lists every
  SKSE DLL in the Ultra profile, with its version check (SE only / AE only / dual), whether it wins or is
  overridden, its Nexus ID, the installed version and the archive it came from. It was generated
  2026-10-18 by reading each DLL's exports and each mod's `meta.ini`.

---

## Status — 2026-10-19

**Done**
- Full instance backup (minus `downloads`): `E:/Zenderal-backups/2026-10-19-pre-AE-migration`. 141,603 files, 0 failed.
- Steam install verified: Enderal **2.1.4.4**, `SkyrimSE.exe` **1.7.104.0**, bundled **SKSE 2.3.1**. **[verified]**
- `Stock game` rebuilt from the Steam install. The old one is in `E:/Zenderal-backups/2026-10-19-stock-game-1.5.97`.
  Left out as non-Steam leftovers: ENB files, screenshots, `ControlMap_Custom.txt`, `binkw64_.dll`, the Apocalypse/EGO/
  `Zenderal - Gameplay Patch` plugins, the xEdit cache, the launcher config/log. Enderal 2.1 now bundles CrashLogger, Engine
  Fixes, Display Tweaks and Address Library in `Data/SKSE/Plugins`, and ships the free AE CC files (`_ResourcePack`,
  Fish, Survival, Curios, AdvDSGS) listed in `Skyrim.ccc`.
- Root Builder's saved state for the old Stock Game (backup + hashes, including the 1.5.97 `binkw64.dll`/`d3dx9_42.dll`)
  was moved to `E:/Zenderal-backups/2026-10-19-rootbuilder-stock-state-1.5.97`, so a Clear can't restore 1.5.97 files.
  Root Builder runs in copy mode with autobuild on. The enabled Root mods are ENB Binaries (ENBSeries 0.504), Engine Fixes -
  Preloader, Steamin ENB, the two `ControlMap_Custom.txt` mods and the junk `Root Builder Test`.
- Restored the reinstall-reset Engine Fixes settings from the backup: `EngineFixes_SNCT.ini` (sound mix) and
  `fSleepWaitTimeModifier = 0.3`.

- **SKSE 2.3.1 Papyrus scripts** installed as MO2 mod `Skyrim Script Extender (SKSE64) Scripts`. It was built from the Nexus 30379
  archive in downloads, sits at the lowest priority (Backend section) and holds 124 files: `Scripts/*.pex` + `Scripts/Source/*.psc`.
  The archive's `skse64_1_7_104.dll` and loader are byte-identical to Enderal's bundled copies, so they weren't duplicated.
  **`game.pex` left out on purpose:** Enderal's own `Game.pex` already contains SKSE's natives plus Enderal's additions
  (10,697 vs SKSE's 10,030 bytes), so SKSE's copy must not override it. `tools.json` → `papyrusSource.skse` now points at the
  mod's `Scripts/Source`.
- User swaps verified by re-scan (2026-10-19 evening): PapyrusUtil AE SE 4.8, Stop On Slash AE (AE file), Fix Note Icon 1.2.6
  (AE file). MCM Helper for Skyrim 1.5, Root Builder Test and both empty PDB mods are gone from the profile.
- SKSE logs live in `C:/Users/frien/OneDrive/Documents/My Games/Skyrim Special Edition/SKSE/` (Documents is redirected to
  OneDrive). The newest `skse64.log` there (17:41) is still from 1.5.97, so **the game has not launched on AE yet.**

**First AE launch: 2026-10-19 20:40** **[verified]**
- When MO2 is started from Claude's sandboxed shell, the game fails with `ERROR_ACCESS_DENIED` spawning `skse64_loader.exe`.
  **The user has to launch from MO2 themselves**; that works.
- It stopped at preload: **Engine Fixes 7.0.20** (mod) can't read Address Library *format 5* (1.7's new format). Enderal
  2.1.4.4 bundles **7.0.21** in Stock Game, so the mod's `EngineFixes.dll` + `.pdb` are now `.mohidden`. The mod's
  `EngineFixes.toml` (same as Enderal's except `fSleepWaitTimeModifier = 0.3`), `EngineFixes_SNCT.ini` and `_preload.txt`
  still apply. Swap the mod to 7.0.21+ from Nexus when it's there.
- Same fix for **SSE Display Tweaks**: its Aug 4 DLL is rejected, while Enderal bundles a newer one (dated 10-19). The mod's
  DLL is now `.mohidden`; its `SSEDisplayTweaks.ini` still overrides Enderal's.
- ENBSeries **0.505** installed into `ENB Binaries/Root` (0.504 DLLs in `E:/Zenderal-backups/2026-10-19-enb-binaries-0.504`).
  The zip is in MO2 downloads with a `manualURL` `.meta` (enbdev forbids hosting the binaries on Nexus).
- `OxygenMeter2` disabled. The CoMAP Enderal patch's `MapMarkerFramework.dll` is `.mohidden`.

**`skse64.log` rejected 45 DLLs.** SKSE scanned 156 plugins. Every DLL below needs a build for 1.7.104 / Address Library
format 5. Any other build loads nothing. Our own Zen DLLs (and Precision) **passed** the check. In MO2 priority order:

| Mod | DLL | Installed | Nexus |
|---|---|---|---|
| powerofthree's Papyrus Extender | po3_PapyrusExtender | 5.10.0 | 22854 |
| ConsoleUtilSSE NG | ConsoleUtilSSE | 1.5.1 | 76649 |
| Enhanced Volumetric Lighting and Shadows (EVLaS) | EVLaS | 1.3.1 | 63725 |
| Payload Interpreter | PayloadInterpreter | 1.1.0 | 65089 |
| dTry Plugin Updates | DtryKeyUtil | 1.0.3 | 85740 |
| Constructible Object Custom Keyword System | CraftingCategories | 1.1.1 | 81409 |
| Mfg Fix | mfgfix | 1.6.1 | 11669 |
| More Informative Console | MoreInformativeConsole | 1.2.2 | 19250 |
| Fix Note Icon for SkyUI | FixNotesForSkyUI | 1.2.6 | 32561 |
| Model Swapper | ModelSwapper | 1.3.0 | 136461 |
| SMP-NPC crash fix | SMP-NPC crash fix | 1.0.0 | 91616 |
| Immersive Equipment Displays | ImmersiveEquipmentDisplays | 1.7.4 | 62001 |
| Simple Dual Sheath | SimpleDualSheath | 1.5.7 | 50049 |
| One Click Power Attack NG | OneClickPowerAttack | NG-v1.11 | 60878 |
| Dual Wield Parrying SKSE | DualWieldParryingSKSE | 1.7.0 | 85505 |
| IFrame Generator RE | MaxsuIFrame | f1.03 | 74401 |
| Combat Pathing Revolution | CombatPathingRevolution | 0.30.0 | 86950 |
| SCAR - Skyrim Combos AI Revolution | SCAR | 0.24.0a | (no id) |
| Modern Stagger Lock | ModernStaggerLock | 1.07a | (no id) |
| Stop On Slash AE | dTryHitStop | 2.2.0 | 66155 |
| Dynamic Animation Casting - NG | loki_DynamicAnimationCasting | 3.2.4 | 73293 |
| FYX - Alpha Blood Blending Bug - NG | AlphaBloodBlendingBug-Fix-NG | 1.0.0 | 149128 |
| Loading Screen Truce | LoadingScreenTruce | f0.01 | 104439 |
| Animation Motion Revolution | AnimationMotionRevolution | 1.5.3 | 50258 |
| Open Animation Replacer - IED Conditions | OpenAnimationReplacer-IEDConditionExtensions | 1.0.2 | 98308 |
| Ultimate Animated Potions NG | UAPNG | 2.8.0 | 97674 |
| FormList Manipulator - FLM | FormListManipulator | 1.8.1 | 74037 |
| Animation Queue Fix | AnimationQueueFix | 1.0.1 | 82395 |
| Paired Animation Improvements | PairedAnimationImprovements | 1.0.2 | 99621 |
| DKAF | DKAF | 1.0.0 | 87706 |
| Sprint Stuttering Fix | SprintStutteringFix | 1.0.0 | 140804 |
| Sprint Sneak Movement Speed Fix | SSMT_Fix | 1.1.2 | 86631 |
| Wade In Water Redone | WadeInWater | 1.1.3 | 71418 |
| TK Dodge NG | TK_Dodge_RE | 1.1.0 | 115408 |
| **RaceMenu** | skee64 | 0.4.20 | 19080 (“incompatible with current version”, needs a 1.7.104 build) |
| Infinity UI | InfinityUI | 2.0.3 | 74483 |
| Local Map Upgrade | LocalMapUpgrade | 3.1.0 | 129756 |
| Hero Menu Enhanced | EnderalHeroMenu | f1.02 | Enderal 563 |
| TrueHUD - HUD Additions | TrueHUD | 1.1.9 | 62775 |
| Compass Navigation Overhaul - Enderal Patch | CompassNavigationOverhaul | 1.1.0 | Enderal 1089 |
| Detection Meter | MaxsuDetectionMeter | 1.11.0 | 63057 |
| CoMAP (patch's DLL now hidden) | MapMarkerFramework | 4.4.0 | 56123 |
| Improved Camera SE | ImprovedCameraSE | 1.1.2 | 93962 |
| Auto Parallax | AutoParallax | 1.0.27 | 79473 |

For each: check the Nexus page for a 1.7.104 / "Address Library v5" build, install it with Replace, and re-launch. Where
none exists yet, decide whether to wait or drop the mod. Dependents matter: TrueHUD (Zenderal - TrueHUD Combat Icons),
Improved Camera (Zenderal - IC Sheathe Fix), Papyrus Extender (many scripts), ConsoleUtil, IED, DTry Key Utils (FHR/combat
keys). The Enderal-specific ones (Hero Menu Enhanced, Compass Enderal Patch) need their Enderal authors, or a rebuild here.

**Why 1.7.104 and not 1.6.1179** **[verified]**: Steam's 2026-09-25 announcement says the Steam release went straight from
1.5.97 + 2.0.12.4 to **1.7.104 + 2.1.4.4**. The only other branch is `enderal_2.0.12.4` (1.5.97). There's no 1.6.1179 on Steam
(GOG has it), and there's no Skyrim SE install on this PC to downgrade from. Every Steam player of the list will be on 1.7.104.
The same announcement says 2.1 saves live in `Documents\My Games\Skyrim Special Edition\EnderalSaves`.

**How SKSE 2.3.1 decides** **[verified from its source, `skse64/PluginManager.cpp`]**: a plugin that sets
`kVersionIndependent_AddressLibraryPostAE` but not `kVersionIndependentEx_AddressLibraryV5` is rejected ("must be recompiled
for new address library") **only if its PE build time is before 2025-05-26**, the `commonlib-shared` commit that added v5
reading. Later builds are let through on trust. So:
- **CommonLibSSE** (`commonlib-shared` line: Enderal's own DLLs, po3's mods, path `_deps\commonlibsse-src` or
  `extern\CommonLibSSE`) built after May 2025 → reads v5. **OK.**
- **New CommonLibSSE-NG** (has `REL/IDDB.h`, the string "Failed to memory-map the address library file"; our `lib/CommonLibNG`
  11.0.0, CrashLogger) → **OK.**
- **Old CommonLibSSE-NG / CommonLibVR** (`REL/ID.h`, e.g. vcpkg `commonlibsse-ng` builds) passes SKSE's check but **pops
  "failed to open address library file" at launch** (Actor Value Generator). **Broken.**

**Hidden for 1.7.104** (renamed `.mohidden`; full paths in `E:/Zenderal-backups/2026-10-19-dlls-hidden-for-1.7.104.txt`).
These are the 28 old-NG/VR DLLs that SKSE lets through:
Native Water Light Stabilizer, wheeler-enderal-fix, BTPS, Smooth Terrain, Dynamic Bloodpool Framework, Sanguine Symphony,
SkyParkour V3, Auto Skeleton Patch, OAR Math Plugin, Skyrim Vanity System, Status Indicator Framework, Death Drop Overhaul,
Next-Gen Decapitations, Dynamic Armor Variants Extended, Core Impact Framework, Lexicon SKSE, Actor Value Generator, dMenu NG,
Papyrus Ini Manipulator, Biggie Traits - Enderal Conversion, Local Map Icons, Break Stagger, Notify Events, TCB, Item Stacking
Tweaks, SKSE Menu Framework, Easy Console Commands, DMK.
Restore one by removing `.mohidden` from its DLL once an updated build is installed. A reinstall via MO2 replaces it anyway.
**Not classifiable** (no library path embedded, so they may still pop up): Casting Bar SKSE Menu Framework, Unsearched Corpse
Indicator, Glow Be Gone Redone - NG, Timed Block-Dodge and Counter, Project Combat Event Fixes, Sound Record Distributor.

**Re-audit (2026-10-19, later)**: `audit17.py` reads every DLL's SKSE version block and build date and applies SKSE 2.3.1's rule.
- 22 of the 28 hidden mods were updated by the user and now pass (V5 flag or the new NG lib): Native Water Light Stabilizer,
  BTPS, Smooth Terrain, Dynamic Bloodpool, Sanguine Symphony, SkyParkour, OAR Math, Death Drop, NG Decapitations, CIF, Lexicon,
  Actor Value Generator, dMenu NG, Papyrus Ini Manipulator, Local Map Icons, Break Stagger, Notify Events, TCB, Item Stacking
  Tweaks, SKSE Menu Framework, Easy Console Commands, DMK.
- Re-hidden (reinstalled at the same old-lib build): Skyrim Vanity System 1.4.10, Dynamic Armor Variants Extended 1.7.5, and the
  new `Skeleton Auto Patch` folder (1.0.4, replaces the removed "Auto Skeleton Patch - Universal Behaviour Runtime").
  Still hidden: Status Indicator Framework 1.0.2.
- Disabled by the user: `wheeler-enderal-fix`, so `Wheeler CTD-Fix`'s 2024 `wheeler.dll` now wins and is rejected, and Wheeler is
  off. Also `Biggie Traits - Enderal Conversion`, which ZenTraitsFixes patches.
- None of the 45 SKSE-rejected mods were updated yet except RaceMenu, whose 0.4.20 only lists 1.6.1170. MO2's `newestVersion` for
  them is stale (`lastNexusQuery` from 2025/Aug 2026), so it doesn't show whether 1.7 builds exist. Papyrus Extender
  (6.5.2) and Combat Pathing Revolution (1.1.6) do show newer versions.

**Launch 21:14 stopped at AltTabFix.** It's built on a CommonLibSSE whose Address Library reader predates v5. That exposed a hole
in the earlier check: the FetchContent folder name `commonlibsse-src` says nothing about the version. **Reliable v5 signature:** the
DLL contains `IDDatabase::load_dense` or "Malformed address library file" (commonlib-shared), or "Failed to memory-map" / `IDDB`
(new NG). An address-library DLL with none of these, which SKSE lets through (built after 2025-05-26, no V5 flag), crashes at launch.
Full re-scan: **68 mods** still have a DLL that won't work on 1.7.104 (`broken17.json` in the session scratchpad).
**User decision 2026-10-19: no more hiding. Find updates and patches, or rebuild.**

**Nexus check of all 68 (2026-10-19 evening).** Files tab read for each.

*Update available, install the named file with Replace:*
| Mod | Have | Get |
|---|---|---|
| powerofthree's Papyrus Extender | 5.10.0 | 6.5.2 (FOMOD: pick 1.7.99+) |
| Spell Perk Item Distributor | 7.3.2 | 7.3.3 |
| powerofthree's Tweaks | 1.16.0 | 1.17.1 (FOMOD: 1.7.99+) |
| Dynamic Location Popups | 1.0.1 | 1.0.2 (FOMOD: 1.7.104+) |
| ConsoleUtilSSE NG | 1.5.1 | 1.6.1 |
| TrueHUD | 1.1.9 | 1.1.10 |
| True Directional Movement | 2.2.7 | 2.3.1 |
| Faster HDT-SMP | 4.0.1 | FSMP 4.1.1 |
| Cached Recursive Directory Walk | 1.1.5 | "CRDW AE" 1.1.5 (25 Aug). The installed DLL is the old reader, so re-download the AE file |
| Knotwork | 2.1.1 | 2.1.2 |
| Alt-Tab Stuck Key Fix | 1.3.1 | AltTabFix 2.0.1 |
| Terrain Helper | 1.0.1 | 1.1.0 |
| Glow Be Gone Redone - NG | 1.5.1 | 1.6 |
| Sound Record Distributor | 1.5.3 | 1.5.4 |
| Auto Parallax | 1.0.27 | 1.0.28 |
| Disable Turn Animation NG | 3.1.0 | 3.2.1 |
| Sprint Sneak Movement Speed Fix | 1.1.2 | 1.1.3 |
| Sprint Stuttering Fix | 1.0.0 | 1.0.1 |
| Paired Animation Improvements | 1.0.2 | 1.0.3 |
| Animation Queue Fix | 1.0.1 | 1.0.2 |
| Ultimate Animated Potions NG | 2.8.0 | 2.9.1 |
| FYX - Alpha Blood Blending Bug - NG | 1.0.0 | 1.0.1 |
| Timed Block-Dodge and Counter | 1.6.0 | 1.7 |
| Simple Dual Sheath | 1.5.7 | "for 1.6.629 and newer" 1.5.9 |
| Project Combat Event Fixes | 1.5.0 | 2.0 |
| EVLaS | 1.3.1 | 1.4.1 |
| SSE Display Tweaks | 0.5.16 | 0.5.25 (then the hidden mod DLL is replaced) |
| dTry Key Utils | dTry Plugin Updates 1.0.3 (its only file is `DtryKeyUtil.dll`) | **not on page 85740**: it has no Key Utils file among the 1.0.4 updates. Take **PaulMix's dTry's Key Utils extend 3.3** (page 141040, 28 Aug, "Support for 1.7.99+") into the existing `PaulMix's dTry Key Utils extend` folder, then disable `dTry Plugin Updates` and `dTry's Key Utils AE` so 3.3 wins |
| Stop On Slash | 2.2.0 (page 66155) | **page 85740** (dTry Plugin Updates): "Stop On Slash" 2.2.1 (24 Aug, "support for 1.7.99"), into the `Stop On Slash AE` folder |
| More Informative Console | 1.2.2 | 1.2.3.1 |
| Constructible Object Custom Keyword System | 1.1.1 | Crafting Categories for SkyUI (27 Aug, "1.7.99") |
| DKAF | 1.0 | "DKAF AE 1.7 Test" 1.1 (13 Oct) |
| One Click Power Attack NG | NG-v1.11 | "One Click Power Attack AE 1.7 Test" (13 Oct, tested on 1.7.104) |
| Combat Pathing Revolution | 0.30 (1.5.97 page 86950) | **different page 146965**: "Combat Pathing Revolution AE" for 1.7.99/1.7.104 (12 Oct) |
| Engine Fixes | 7.0.20 (mod DLL hidden) | "7.0.21 beta for Skyrim AE 1.7.99" (says 1.7.99 only). Enderal bundles 7.0.21 already, so keep using Enderal's |
| Skeleton Auto Patch | 1.0.4 | "Pandora XPMSE Behavior Patch" 1.0.0 (no DLL; use it *instead of* the SKSE plugin) |

*No 1.7 build on Nexus (newest file predates 1.7, or is labelled 1.5.97/1.6.x only):* RaceMenu 0.4.20, Improved Camera SE 1.1.2,
Immersive Equipment Displays 1.7.4, TK Dodge NG 1.1.0, Dual Wield Parrying (1.6.1130+ file), Dynamic Animation Casting NG 3.2.4,
IFrame Generator RE, Animation Motion Revolution 1.5.3, Payload Interpreter 1.1.0, OAR IED Conditions 1.0.2, SMP-NPC crash fix,
Model Swapper 1.3, FormList Manipulator 1.8.1, Mfg Fix 1.6.1, Casting Bar 3.0.0 (source on Nexus), Oxygen Meter 2 Fixes 1.0.8
(source on Nexus), Unsearched Corpses Indicator 1.3.2, RaySense Cover 1.5, Auto Physics Reset 1.3, Local Map Upgrade 3.1.0,
Infinity UI 2.0.3, Wheeler 1.2 / Wheeler CTD-Fix 1.0.1 / wheeler-enderal-fix 1.0.0, Loading Screen Truce
(1.5.97 only), Fix Note Icon (AE 2.2.x file, 2022), Status Indicator Framework 1.0.2, Skyrim Vanity System 1.4.10 (GPL, GitHub),
Dynamic Armor Variants Extended 1.7.5 (GPL, GitHub), Detection Meter (AE file is v0.16 from 2022), Hero Menu Enhanced 1.02,
Compass Navigation Overhaul - Enderal Patch 1.1 ("tested on 1.5.97 and 1.6.1179"). Plus SCAR and Modern Stagger Lock (no
Nexus ID in MO2). For these the options are wait, find a community 1.7 fork, or **rebuild from source against `lib/CommonLibNG`
11.0.0**, which reads v5. Many are open source (SVS, DAVE, Casting Bar, Oxygen Meter 2, and the D7ry/Maxsu/ersh plugins).

**Stock Game + Root Builder check** **[verified]**: the 21:14 launch ran SKSE 2.3.1 on 1.7.104 from `Stock game`, and 12 plugins
loaded before AltTabFix. Root Builder built on launch, synced back, cleared on exit and restored its backup. Stock Game's root is
now clean (no leftover ENB/preloader files), and its state folder is `plugins/data/rootbuilder/EZenderalStock_game/0_2_3_1`.

**Re-scan after the user's update pass (2026-10-19 night).** Scanner: `broken17.py` in the session scratchpad.
- **27 more fixed:** Papyrus Extender, SPID, ConsoleUtil, TrueHUD, TDM, FSMP, Knotwork, DLP, Terrain Helper, Glow Be Gone, Auto
  Parallax, AltTabFix, DKAF, OCPA, CPR (AE page), Project Combat Event Fixes, Sound Record Distributor, More Informative Console,
  Crafting Categories, Sprint Stuttering Fix, Paired Animation Improvements, Animation Queue Fix, UAP NG, Disable Turn Animation,
  FYX Alpha Blood, Timed Block-Dodge and Counter, and Skeleton Auto Patch (switched to its DLL-free Pandora patch).
- **Probably fine, despite the scanner:** Sprint Sneak Movement Speed Fix 1.1.3, Simple Dual Sheath 1.5.9, SSE Display Tweaks
  0.5.25, EVLaS 1.4.1. They use their own (non-CommonLib) Address Library loader, rebuilt Aug/Sep 2026 with the author claiming 1.7,
  so the CommonLib signature can't judge them. Confirm in `skse64.log`.
- **Still the old reader, with no newer Nexus file:** CRDW 1.1.5 "AE" (po3 CommonLibSSE copy older than SPID 7.3.3's). Not yet
  installed: po3's Tweaks 1.17.1, PaulMix Key Utils extend 3.3 (+ disable `dTry Plugin Updates`, `dTry's Key Utils AE`),
  Stop On Slash 2.2.1.
- CoMAP 4.4 and base Wheeler 1.2 DLLs are also "must be recompiled". The patch/fix layers over them are disabled or hidden.
- **Settings wiped by updates, restored** (a value counts as "yours" when the pre-update file differed from the original archive's
  default). Backups of the post-update files are in `E:/Zenderal-backups/2026-10-19-configs-before-restore`:
  - SSMT_Fix `WieldingMovementTypeFixes=true` (FasterSprint needs it)
  - TimedBlockDodgeCounter.ini: all 24 tuned values (parry 220 ms, hitstop 0.25, counter +140 %/2 s, slow-mo/timed-dodge off, volumes)
  - SKSE Menu Framework `ToggleKey=F7`
  - SSEDisplayTweaks `Fullscreen=false`, uncommented
  - FSMP `disableSMPHairWhenWigEquipped=false`
  - Oxygen Meter scale 50 (done earlier)

**Our DLLs rebuilt for SE + AE (2026-10-19, 22:06–22:45)** **[verified: build + static check; not yet in game]**
- Every Zenderal SKSE DLL had been built `ENABLE_SKYRIM_SE ON / ENABLE_SKYRIM_AE OFF`, so it knew only the SE file name
  `version-*.bin` and popped "failed to open address library file" on 1.7.104. The earlier "our DLLs passed" claim was wrong:
  they had only passed SKSE's flag check.
- `CMakeLists.txt` → `ENABLE_SKYRIM_AE ON` (SE kept ON, so one DLL covers 1.5.97 and AE) for BlockReleaseFix, CCCStandDown,
  CrossbowDrawFix, DBVOPlayerLipSync, DBVOSexDefaults, GamepadCombos, ImprovedCameraSheatheFix, MusketHandling and
  TrueHUDCombatIcons. All nine built with exit 0 against `lib/CommonLibNG` 11.0.0. Each has the `versionlib-{}.bin` name, the
  IDDB/v5 reader and SKSE's V5 flag.
- PrecisionFork: `upstream/` (ersh1/Precision `9ef45e0`) and `lib/CommonLibNG-8339e6d` were re-cloned (both gitignored), the patch
  re-applied cleanly, and `build.cmd` → `-DENABLE_SKYRIM_AE=ON`. On 1.7.104 the ragdoll fix logs "not 1.5.97 - addresses unknown,
  nothing patched" and Precision runs as upstream 2.0.6. **Porting the three hook addresses (`0x9EC0B5`, `0xB16228`, `0x9ED4B5`) to
  1.7.104 needs a memdump run** (`tools/memdump`), because the AE exe is DRM-encrypted on disk.
- Deployed to `compiled/`, each standalone `Zenderal - *` MO2 mod and `Zenderal - Patch Collection`. The old 1.5.97 DLLs are in
  `E:/Zenderal-backups/2026-10-19-zen-dlls-1.5.97`.
- Not rebuildable: ChocolatePoiseEnderal's `ZenCPRFactionFix` / `ZenChocolatePoiseFix` are .NET Script Framework plugins (no AE NSF),
  so they need a rewrite as SKSE plugins. ImprovedCameraSheatheFix patches IC 1.1.2's DLL, so it does nothing until IC has a 1.7 build.

**Community 1.7.104 alternatives on Nexus (2026-10-19, via the public GraphQL API at `api.nexusmods.com/v2/graphql`)**
Each one installs below the original mod and only replaces its DLL, unless the row says otherwise:
| Broken mod | Alternative (Nexus ID) |
|---|---|
| Immersive Equipment Displays 1.7.4 | IED - 1.7.104 Update (195107): binary patch of the 1.7.4 DLL |
| OAR IED Conditions | Open Animation Replacer - IED Conditions - OAR 3.x Update (191990) |
| Modern Stagger Lock 1.07a | ModernStaggerLock - AE 1.7.104 Unofficial Patch (195580): recompiled, source linked |
| Payload Interpreter | Payload Interpreter - Skyrim 1.7.104.0 Update (192679) |
| Animation Motion Revolution | AMR - Skyrim 1.7.104.0 Update (191697), 1.5.4 |
| Dynamic Animation Casting NG | DAC NG - 1.7.104 Update (194024) |
| IFrame Generator RE | IFrame Generator RE AE Support (82737), 24 Aug, "support for 1.7.99" |
| Detection Meter | Detection Meter - Skyrim 1.7.104.0 Update (191692) |
| FormList Manipulator | FLM NG (193349) 1.8.2, drop-in, GPL source |
| Mfg Fix | Mfg Fix NG (133568) 1.0.10, "1.5.97, 1.6.117x, 1.7.x" (a different mod; check API compatibility) |
| Loading Screen Truce | Loading Screen Truce AE (104522), 8 Sep 2026 |
| Oxygen Meter 2 - Fixes and Additions 1.0.8 | Oxygen Meter 2 SKSE 1.7.104.0 (195918): "OxygenMeter2 1.0.8 1.7.104" DLL |
| Infinity UI | Infinity UI NG (192919) 2.1.2 |
| Local Map Upgrade | Local Map Upgrade SKSE Menu Framework (189625) 1.3.3, a fork for 1.5.97/1.6.1170/1.7 |
| Compass Navigation Overhaul | CNO SKSE Menu Framework fork (189628). Doesn't mention Enderal, so it may lose what the Enderal patch fixed |
| Wheeler | Perfected Wheeler (191722), a fork of Wheeler - Refined that needs ApocryphaRealm Menu Framework. The Enderal bow CTD is untested |
| CoMAP | **rebuilt here** from Exit-9B's repo (2.2.2, has the 1.7.99 fix) → deployed. Originals in `E:/Zenderal-backups/2026-10-19-thirdparty-dll-originals` |
| TK Dodge NG 1.1.0 | **rebuilt here** (2026-10-19) from itahol/TK-Dodge-NG `d6b8efc` (MIT) against `lib/CommonLibNG` 11.0.0, SE+AE. The source sits in `lib/rebuilds/TKDodgeNG` (gitignored), built with `zen-build.cmd`. Ported: the CommonLib path, NG-11 `SKSEPluginInfo`/`SKSEPluginLoad`, `RestoreActorValue`→`ModActorValue` (same vfunc 06), the `magic_enum/` include, `NOMINMAX`, CLibUtil from `powerof3/CLibUtil` headers. Output: 1.1.0, V5 flag, v5 reader, static CRT. **Deployed; not yet tested in game.** No other 1.7 build or fork exists (the two GitHub forks are commit-identical to upstream; TK Dodge Redux 3.6.2 is June 2026) |
| Dual Wield Parrying SKSE 1.7.0 | **rebuilt here** (2026-10-19) from DennisSoemers/DualWieldParryingSKSE `d1ff693` (v1.7.0, Apache-2.0) against `lib/CommonLibNG` 11.0.0, SE+AE. Source in `lib/rebuilds/DWP`, built with `zen-build.cmd`. Ported: dropped the Color-Glass vcpkg port and the unused `articuno`/`ryml`; CommonLib via `add_subdirectory` + its `cmake/CommonLibSSE.cmake` `add_commonlibsse_plugin(... USE_ADDRESS_LIBRARY)`; SimpleIni found by `SimpleIni.h`; `NOMINMAX`; LTCG off; keyboard `IsPressed` done inline (CommonLib's out-of-line one links `BSWin32KeyboardDevice.cpp`, whose engine virtuals are undefined → LNK2001). Output: name/version/exports identical to 1.7.0, V5 flag, v5 reader. Restored the user's 1.7.0 folder (ParryKey 258) from the pre-migration backup first. The Nexus "1.6.1130 and above" NG 2.0.1 install (`DualWieldParryingNG.dll`, Mar 2024, rejected on 1.7.104, ParryKey reset to 47, ini renamed so it would break ZenBlockReleaseFix) was saved to `E:/Zenderal-backups/2026-10-19-dwp-ng-2.0.1-as-installed`. In NoMatchInclude. **Deployed; not yet tested in game** |
| Status Indicator Framework 1.0.2 | **rebuilt here** (2026-10-19) from JerryYOJ/Status-Indicator-Framework-SKSE `8f971e2` (GPL-3.0). That commit is the installed 1.0.2: its DLL was built at 06:38:49 UTC, 28 s after the commit. No source changes; new `zen/CMakeLists.txt` mirrors the repo's `.buildenv` but adds CommonLibNG 11 via `add_subdirectory`, SE+AE, `USE_ADDRESS_LIBRARY` and `NOMINMAX`. Output: name `StatusIndicatorFramework`, internal version 0.0.1 (as upstream), V5 flag, v5 reader, static. Unhidden and deployed; original + stale PDB in `2026-10-19-thirdparty-dll-originals`; in NoMatchInclude. Hooks attach at function starts by ID (50781/51676, 50782/51677), and two data reads use fixed offsets (+0x40/+0x44) into ID 517032/403540, so 1.7 layout changes would show in game. **Not yet tested in game** |
| Dynamic Armor Variants Extended 1.7.5 + Skyrim Vanity System 1.4.10 | **rebuilt here** (2026-10-21) from PenguinToast/DynamicArmorVariants-Extended `0c2244e` (tag v1.7.5, MIT) and PenguinToast/SkyrimVanitySystem `9f9514f` (tag v1.4.10, GPL-3.0) against `lib/CommonLibNG` 11.0.0, SE+AE. Sources in `lib/rebuilds/DAVE` and `lib/rebuilds/SkyrimVanitySystem` (gitignored), each with a `zen/CMakeLists.txt` mirroring its `xmake.lua` and `zen-build.cmd`. SVS needs DAVE, so both were hidden/disabled together. Ported: `SKSEPluginLoad(...)` for the removed `SKSEAPI` export, DAVE's `spdlog::string_view_t` → `std::string_view`, SVS's private `RE::GFxCharEvent` dropped for CommonLib's (`wCharCode`, same offset 04). **Every hook site checked in the 1.7.104 exe** (capstone + `versionlib-1-7-104-0.bin`): SVS's four call sites (PollInputDevices 68617+0x7B, RegisterClassA FF15 at 77226+0x15C, InitD3D 77226+0x2BC, Present 77246+0x9) and DAVE's whole-function replacements are where expected; the skill-leveling hook (38627+0x3EE) byte-verifies at runtime. **One DAVE fix:** at FixEquipConflictCheck 38004+0x97 upstream read the armor from `[rsp+0x88]` in its patch, i.e. the function's callee shadow slot +0x18, which only holds the item because callee 16040's prologue parks rbx there; the outer slot loop's later calls can overwrite it. Changed to the item's own arg spill (`[entry+0x10]` = caller rsp+0xD8, restored by the function at +0x270) → patch offset 0x148. RaceMenu compat: DAVE's layouts stop at RaceMenu 0.4.20, so on our 0.5.0 b6 it logs "unsupported version" and skips (no crash; RaceMenu overlays on variant-swapped armor may not follow). Output: 1.7.5 / 1.4.10, V5 flag, v5 reader, static. Originals + PDBs in `2026-10-19-thirdparty-dll-originals`; DAVE's DLL un-hidden, SVS re-enabled in Ultra; both in NoMatchInclude. **Not yet tested in game**: open SVS (F6), preview/apply an override, check `DynamicArmorVariants.log` for "Equip conflict" installed |
| Compass Navigation Overhaul (Enderal patch DLL) | **rebuilt here** (2026-10-20) from alexsylex/CompassNavigationOverhaul `4055b00` (MIT). Its DLL code is identical to `f39e969`, the namespace-`CNO` + `NND/` layout the Enderal patch DLL was built from; later commits only touch SWF sources. Deployed over the Enderal patch's DLL (the winner); the installed 2.2.0 Interface SWFs stay. **Why the Enderal patch existed:** `HUDMarkerManager.h` did `LookupByID(0x02014217)->As<TESFaction>()` (Dawnguard) etc.; Enderal's Dawnguard.esm is a stub, so this was a null dereference. Fixes: a null-safe `LookupFaction()` for all 5 factions plus early-out in `IsPlayerAlly/OpponentOfFaction`. NG-11 port: the old `Offset::` table → the same `RELOCATION_ID`s NG 11 uses (18 GFxValue::ObjectInterface + `EnsureQuestStarted` 24481/25003 + `ResetQuest` 24486/25014); `SKSE::WinAPI` → Win32; `Setting` renames (`kInteger`, `GetInteger`, `GetUnsignedInteger`); objectives via `GetPlayerRuntimeData()` (NG 11 handles the 1.7.99 layout shift); CNO's duplicate `NiPoint3.cpp` cut to its own `GetHorizontalAngleTo`; Xbyak on. **New guard:** CNO's MapMarkerFramework compat hook pattern-scans CoMAP's DLL. The pattern only exists in the old Enderal Map Markers DLL (now hidden), not in CoMAP 2.2.1/2.2.2, and a miss used to write a hook at address 6, so it is now skipped with a log warning. Output: 2.2.0, V5 flag, v5 reader, static; in NoMatchInclude. **Not yet tested in game**: check the compass, quest list, and whether CoMAP markers show on it (the compat hook is off) |
| Model Swapper | Only one enabled mod uses it: *HFs - Buttocks rest* (its only `_MS.json`). That mod's page (146910) also has "HFs - Buttocks rest (BOS) - 2K/4K" (ESL plugin, Base Object Swapper), so swap to the BOS file and disable Model Swapper |
| Improved Camera | Its Discord (betas): https://discord.gg/Hr7pRchWcf (from the Nexus page and the TDM-IC patch page). Wabbajack CDN has `Improved Camera v2.7z` (TwistedModding / Twisted Skyrim, uploaded 2025-04-24): IC **2.0.0**, built 2025-04-22, flags (1,1). **SKSE 2.3.1 rejects it on 1.7.104** like 1.1.2. Not usable |
| SCAR | SCAR AE Support (77285) v1.06.2, 24 Aug 2026: "support for Skyrim 1.7.99" |
| Model Swapper | nothing on Nexus, no GitHub forks. MIT source (Thiago099/Model-Swapper), so it can be rebuilt |
**Not a match:** DynamicArmorVariants-1.7.104-Patch (189578) is for the *original* DAV, not PenguinToast's Extended. SJG's Dual
Wield Parrying is a 2018 Papyrus mod, not a DLL replacement.
**No alternative found:** RaceMenu, Improved Camera (its author's v2.0 beta is Discord-only), TK Dodge NG, Dual Wield Parrying SKSE,
SCAR, Fix Note Icon, Model Swapper, SMP-NPC crash fix, Skyrim Vanity System, DAVE, Status Indicator Framework, Unsearched Corpse
Indicator, RaySense Cover, Auto Physics Reset, CRDW, Hero Menu Enhanced, Compass Enderal Patch.
**Catch-all tool:** *CompaSSE* (190307) patches old pre-1.7 CommonLib DLLs in place (version flags, a per-plugin Address
Library format shim, hook re-resolution), with backups and one-click undo. Its own page says it targets abandoned *old* plugins
and won't fix modern ones. The user would run it themselves.
*SKSE Crutch Pack 1.7.104* (195854) covers none of our mods.

**Outstanding as of 2026-10-19 late** (`broken17.py` re-scan plus a check of the last SKSE log)
- The 22:40 launch reached SKSE's data-loaded messages (type 8) with 120 plugins loaded, so **the game boots on 1.7.104**. That
  was before the evening's updates.
- 14 more fixed by installs: RaceMenu 0.5.0 b6, IED 1.7.104 Update, TK Dodge (rebuilt), Payload Interpreter, DAC, Modern Stagger
  Lock, IFrame Generator, Detection Meter, FLM, Loading Screen Truce, Infinity UI, Local Map Upgrade, Mfg Fix, OAR IED Conditions.
  No settings were lost in that batch.
- Unverified: the *AMR - Skyrim 1.7.104.0 Update* DLL has no V5 flag and an NG reader the signature check can't place (built
  2026-09-10). Read the next `skse64.log` and its own log.
- Still hidden: Status Indicator Framework 1.0.2, DAVE 1.7.5. (The EngineFixes mod DLL and the CoMAP Enderal patch DLL are
  hidden on purpose.)
- Still skipped by SKSE: Improved Camera 1.1.2, Wheeler (CTD-Fix copy), Compass Navigation Overhaul - Enderal Patch, Hero Menu
  Enhanced, SCAR, Dual Wield Parrying SKSE, SMP-NPC crash fix, Model Swapper, Fix Note Icon.
- Disabled for 1.7: CRDW, Auto Physics Reset, RaySense Cover (+ Zenderal RaySense Priority), Skyrim Vanity System, Unsearched
  Corpse Indicator, Casting Bar SKSE Menu Framework (plain Casting Bar on), wheeler-enderal-fix, Biggie Traits, BEES, .NET Script
  Framework.
- In-game test pass not started.

**Launch 2026-10-20 00:31 (verified in `skse64.log`):** 140 plugins "loaded correctly", including AMR 1.7.104 Update (its own log
says "Succesfully loaded!", so the old-reader flag was a **false positive**: its NG build reads v5 without the signature strings),
our rebuilt DWP, TK Dodge, SIF, Precision Fork, CoMAP, SCAR AE and TDM 2.3.1, plus all Zen DLLs. Rejected: only
CompassNavigationOverhaul.dll and wheeler.dll. The user had unticked *Compass Navigation Overhaul - Enderal Patch* (where the
rebuild lives), so it was re-enabled; *Wheeler CTD-Fix* (only an old wheeler.dll) was disabled so *WHEELER - Refined* 1.3.4
(installed by the user, DLL passes, ships its own assets) wins. After that the re-scan shows nothing left but deliberately hidden
DLLs and DAVE.

**Launch 2026-10-20 00:35: CTD at load in FormList Manipulator NG 1.8.2** (Nexus 193349, a clean-room reconstruction of 1.8.1).
`crash-2026-10-20-00-35-19.log`: `FormListManipulator.dll+0x8474` in `Manipulator::addFormPair`, reading `[null+0x30]` in the PLANTS stage.
FLM fills `lists_` with 11 vanilla FormLists by EditorID (`flPlanterPlantableItem`/`flPlanterPlantedFlora`, BYOH adoption toys,
`HairColorList`, Atronach Forge, DLC2 spider crafting). Most are absent in Enderal, so the entries are nullptr, and `addForms`/`addFormPair`
dereferenced them. **Rebuilt here** from the GPL source zip (user-downloaded into MO2 downloads) with a missing-list guard in both
functions (logs and skips, which is effectively what the original 1.8.1 did), against CommonLibNG 11 via the project's own
`COMMONLIB_SSE_FOLDER` path; VR off; vcpkg moved to our baseline (the old fmt 9/spdlog 1.11 pins dropped). Source in
`lib/rebuilds/FLMNG` (originals `*.orig`). Output 1.8.2, V5, v5 reader, static. Deployed; the stale PDB was moved to backup; in NoMatchInclude.

**Display settings after the update:** SSE Display Tweaks 0.5.25 loads `SSEDisplayTweaks_custom.ini` and lets it override the main ini
("Custom configuration loaded" → "Resolution override: (1920x1080)" from the shipped 16x9 preset). The user's ultrawide had only set
`Resolution=3360x1440` in the main ini of the Wabbajack-ignored *Zen's Ultrawide - 3360x1440 - Do not use* mod. Fix: that mod now
also ships `SSEDisplayTweaks_custom.ini` with `Resolution=3360x1440`. It's higher priority than the presets and ignored by the compile.

**Main menu reached, then 2.1 content issues (2026-10-20):**
- *"OUTDATED MOD: Levelsystem"*: 2.1 removed `_00E_Game_SkillmenuSC` (level system moved into `EnderalSE.dll`). Our
  recompiled copy was removed from *Zenderal - Controller Tweaks* and *Zenderal - Patch Collection* (backup
  `E:/Zenderal-backups/2026-10-20-skillmenusc-removed`; repo source in `src/ControllerTweaks/retired-enderal-2.0/`). The B+D-pad-Up
  Hero Menu chord is gone until it is reimplemented for 2.1. `KataPUMBAffinities.esp` also overrides QUST `010AA2` (Levelsystem):
  the user is disabling KataPUMB New Affinities, its EGO patch and the Amnesia KataPUMB add-on, and updating Amnesia Shrine to v4.00.
  **Later on 2026-10-20 Kata's affinities were ported back:** [`KataAffinities21`](../patches/KataAffinities21.md)
  ports its 24 affinities into 2.1's `_00E_AffinityControl` and fills them on `AffinityControl 01597B`, on a generated
  cleaned Kata copy (no `010AA2`, no skill-menu `.pex`). The EGO patch is back on; the Amnesia add-on stays retired.
- **Duplicate races in chargen**: 2.1 moved the playable races to `013746`/`013748`, and EGO's three race plugins still make the
  old `033899`/`033898` playable. Fixed by the new **[`EGO21Compat`](../patches/EGO21Compat.md)** patch (deployed after DS Unique
  Races; it wins all four RACEs in a load-order scan). Unverified in game. EGO's NPC/ARMA/FLST old-race refs are still to remap.
- 2.1's masters were decompiled into **`reference/base-2.1.4.4/{Skyrim,Update,EnderalFS}`** (Spriggit 0.40.0; only the
  round-trip self-check fails, as for 2.0's Skyrim.esm). `reference/base/` is still 2.0.12.4: the swap failed because a handle was
  open on `reference/base/Skyrim`. Swap it (2.0 → `reference/base-2.0.12.4`) once nothing holds it, then grep `base/` as before.
- *Fuse00 Armor Races* is redundant on 2.1 (the addons' own `013746`/`013748` now match the playable races); harmless.

**Script-version popups (2026-10-20).** EnderalSE.dll 2.1 calls a static `_GetScriptVersion()` on 76 SureAI
scripts at the first load (list in `Util.h` of `Data/SKSE/Plugins/fs_src.zip`) and pops *"Script X is overwritten by
a mod ... installed version: N/A"* when the winning copy lacks it or fails to link. Four fired:
- `_00E_EPUpdateFunctions` — our Fever Death Latch Fix (2.0 base) → rebased onto 2.1 source.
- `_00E_Theriantrophist_PlayerAsWerewolf` — EGO (and Bug Fixes) → 2.1 + EGO's edits, shipped by EGO21Compat.
- `_00E_GUI_ActorHealthBar` — *Remove Ally Hud Bars*' 0-byte pex → replaced by Settings Applier defaulting
  `_00E_ActorHealthBarsEnabled` to 0. **The mod still has to be disabled in MO2.**
- `_00E_EnderalMCM` — no override at all: it failed to link because its property type was the blanked script
  above. Fixed by the same step.
2.1's full script source is unpacked in `papyrus-source/enderal-2.1.4.4/source/scripts`, and `tools.json`'s
`papyrusSource.enderal` now points there (it has the base types, SKSE, SkyUI and the flags file).
`papyrusSource.vanilla` is stale (the Nemesis mod it pointed into is gone), and the PapyrusUtil `importDirs`
entry points at the renamed 1.5 mod. Compiling from the compiler's own folder with only our source + 2.1 + SKSE
works. Papyrus logging is on in the Ultra profile (`Enderal.ini`, backup in
`E:/Zenderal-backups/2026-10-20-papyrus-logging`) — turn it back off after the test.

**2.1 changelog / official repo cross-reference (2026-10-20).** Source: `Data/Enderal SE v2.1.4.4 Changelog.txt` and
`git.eddoursul.win/enderal/enderalse` (branch `development`).
- 2.1.4 *"Fixed meshes appearing too bright under shadows during daytime"* = commit `23eb96a9f8` (2025-08-02, "Hortophyll:
  fixed mesh lighting following Catnyss' instructions", 596 meshes). It is *Enderal - Fixed Mesh Lighting* (Nexus 826)
  merged into base: emissive multiple 1.0 → 0.0 on grass/flora/trees with black emissive colour. **[verified]** our loose
  FML copies already equal 2.1's, so FML is now redundant (harmless). Any third-party grass/flora mesh with emissive mult
  1.0 brings the glow back: SFO-stripped did, and the EGR block has ~300 such shapes (Tamrielic 135, Folkvangr 109,
  Cathedral 38, EGR 10 incl. its copies of 2.1-fixed clovers, Rock Grass 3, Origins 2, 3D Pine 2).
- 2.1.0 race remap → EGO21Compat. Levelsystem refactor → SkillmenuSC retired, KataPUMB New Affinities ported (KataAffinities21), Amnesia 4.00.
  Script version control → the popups. MCM companion-health-bar toggle → replaces Remove Ally Hud Bars.
- 2.1.4 regenerated LOD (xLODGen beta 132 / DynDOLOD 3 alpha 194): *DynDOLOD Output - Zenderal* was built on 2.0 and
  overrides it → regenerate (Phase 6). 2.1.4 / 2.1.4.4 alchemy revisions (`fAlchemySkillFactor=4.5`,
  `fAlchemyIngredientInitMult=1.0`) → audit EGO's and our alchemy/potion records against them (Phase 5).
- 2.1.4.3 added widescreen support and refuses to start with *Widescreen Scale Removed*; SkyUI 6 support.
- No changelog entry or commit mentions grass placement/height; the floating look is not from a documented 2.1 change.

**ENB → Bottled Shaders (2026-10-20).** ENB complex grass does not apply on 1.7.104 (0.505 and 0.504 both tested; the
1.7 shader pack `shaders011.fxp` changed and enbdev has shipped nothing since 2026-08-05), so complex-grass textures drew
their packed normal-map half: grass looked raised, rock grass rainbow. Switched to **Bottled Shaders 1.0.18** (Nexus 192816,
a Community Shaders fork with every CS feature bundled, Effects 11, reverse-Z, seasons) + **Light Placer 5.0.0** (Nexus
127557, the "v1.7.104+" DLL) + **CS Light 2.0.1** (Nexus 138443).
- Disabled: ENB Binaries, ENB Extender and Helper, ENB World Map Fix, EVLaS (CS-incompatible), Terrain Helper (bundled in
  Bottled; identical `TerrainHelper.esp`). Kept: *Steamin ENB* so Effects 11 runs its preset (Shift+Num* toggles).
- Grass back on the complex builds (EGR ENB, Tamrielic for ENB Complex Grass, Rock Grass for ENB Complex Grass);
- **Unified Water off (2026-10-21).** Bottled Shaders' *Unified Water* ("replaces distant water tiles with LOD0",
  per-worldspace cache `overwrite/SKSE/Plugins/CommunityShaders/UnifiedWaterCache/<ws>_cache.wc`) drew flat grey
  hard-edged tiles over the sea, even right next to the camera in loaded cells. Confirmed by an A/B test with it in
  *Disable at Boot*: the tiles were gone. A freshly rebuilt cache still showed them, and the feature has no options.
  Earlier terrain-LOD suspects did not fix it: a stray 2.0-era loose `vyn.32.-5.9.btr` (moved to backups) and a
  fresh xLODGen terrain LOD (kept, as it matches the landscape mods). **The CS settings now ship in *Zenderal -
  Settings*** (`SKSE/Plugins/CommunityShaders/SettingsUser.json`, moved out of overwrite, which Wabbajack misses),
  with Disable at Boot = GrassOptimizations, HDRDisplay, PostProcessing, Skin, UnifiedWater. Don't toggle CS features
  live under MO2: the runtime recompile of ~1500 shaders failed to open its includes and crashed (02:07, alt-tab).
  Use Disable at Boot and restart.
  *Zenderal - Grass Lighting Fix* regenerated for them (297 meshes).
- CS Light audit: all 30 effect-shader EditorIDs and every light-template EditorID exist in Enderal; 779/1093 mesh
  entries hit meshes that exist (the rest no-op); `CS Light.esp` (ESL, Skyrim.esm master) overrides 21 magic LIGH that
  only Skyrim.esm defines in this list. Skyrim-city window, mod-patch and Creation Club configs not installed.
- Per Theo's page: in the CS menu turn **Frame Generation and Reflex off, keep Upscaling on**. ENB light/particle-light
  mods no longer light anything under CS (CS Light's page); judge Water for ENB / Darker Distant LOD for ENB in game.
- **PGPatcher 2.3.1** (Nexus 120946, tool in `Tools/PG Patcher`; 1.2.0 backed up) run from MO2 2026-10-20 (2.x refuses
  to run outside MO2: "VFS not detected"). Settings: game type 3 (= Enderal SE, as the working 1.2.0 run), CM + parallax
  + TruePBR on, parallax→CM upgrade on, Fix Mesh Lighting off (ENB-only), fix SSS + disable pre-patched materials on,
  hair flow maps off, vanilla BSA list = Skyrim - Textures0-8 + E - Textures1/2. Result: 41256 meshes / 60240 textures,
  67 s, 3 unreadable files. Output mod *PG Patcher Output* (top priority): `PGPatcher.esp` (ESM+ESL, 173 TXST) +
  `PG_1.esp` (ESL, 1683 base-object overrides, 25 masters), both before Occlusion.esp / DynDOLOD.esp. *Auto Parallax*
  disabled (PGPatcher: "edits the same materials"). The tool-as-mod *PGPatcher* MO2 created is disabled.
  DynDOLOD.esp overrides 7 of PG_1's statics (Bridges of Enderal ×3, EPPI ×2, Old Watermill, Wellwatch Manor) and wins
  them until TexGen + DynDOLOD are regenerated after PGPatcher (they are 2.0-era anyway). **Re-run PGPatcher after any
  mesh/texture mod change.**
- Not done yet: first-launch SKSE/BottledShaders.log check; TexGen + DynDOLOD regeneration.

**Still to do before the next AE launch**
- [ ] Enderal Map Markers - CoMAP Patch: the only 1.5.97-only DLL still winning. Hide its `SKSE/Plugins/MapMarkerFramework.dll`
      (MO2 Data tab → right-click → Hide); CoMAP's AE DLL is underneath.
- [ ] Disable `OxygenMeter2`. It's a losing 1.5 copy, and its `.ini` would still shadow nothing, but it's clutter for the compile.
- [ ] Beard Mask Fix + Constructible Object Custom Keyword System are AE-only and now load. Keep or disable.
- [ ] ENBSeries 0.504 (`ENB Binaries`): check enbdev for 1.7.104 support.

**First launch, then**
- [ ] Launch to the main menu and read `skse64.log`. SKSE 2.3.1 flags "plugins that need to be rebuilt due to the address
      library change" on 1.7, so **AE-only DLLs aren't guaranteed to load on 1.7.104**. The log is the check for every DLL.
- [ ] Zenderal - Patch Collection: its 1.5 DLLs (incl. `Precision.dll`, which outranks Zenderal - Precision Fork) → Phase 4.
- [ ] Pandora's `ActiveMods.json`/`PreviousOutput.txt` lived in the old Stock Game's `Data/Pandora_Engine` and are gone. Re-tick
      zpaired + zpairset at the next Pandora run.

---

## Strategy — what makes this smooth

1. **Swap in place, keep folder names.** Install each AE build into the *same* MO2 mod folder (MO2 →
   install → **Replace**). Load order, the Wabbajack compile settings, `user.json`/ini overrides and
   every doc that names a mod all stay valid. The alternative is parallel `[AE]` folders, which doubles
   the list and breaks the compile's Include rules.
2. **Back up only what you replace.** The DLL mods are small. Before replacing a folder, copy it to
   `E:/Zenderal-backups/1.5.97-mods/`. Never put backups inside `E:/Zenderal`: stray files there break
   the Wabbajack compile. Rolling back means restoring those folders plus the old Stock Game.
3. **Download everything first, install later.** Go through Phase 2's table and pull every AE archive
   into MO2's downloads (*Download* only, don't install). The swap itself is then an afternoon with no
   Nexus round-trips, and every archive keeps its Nexus source in `meta.ini`, which Wabbajack needs.
4. **Bring the game up in layers, using `skse64.log` as the referee.** First a bare profile (SKSE +
   Address Library + Engine Fixes), then the frameworks, then everything. After each layer, read
   `My Games/Skyrim Special Edition/SKSE/skse64.log`. SKSE lists every plugin as loaded or rejected, so
   a DLL that doesn't support 1.7.104 says so there. That is the only real proof for the ~120 "dual"
   DLLs, which can't be checked by inspecting them.
5. **Content comes after code.** Enderal 2.1 changed its ESM: an alchemy rework, Restore Health moved
   to `3EB15`, many record fixes. Once the game boots, diff the old and new ESMs and re-check every mod
   and patch that overrides a changed record. That's Phase 5, and it is the part most likely to hide
   silent breakage.

---

## Phase 0 — Prep (the live list stays untouched)

- [ ] Note Wabbajack's consequence: Steam will auto-update players' Enderal as well. The published
      1.5.97 list stops installing for them, so plan the release timing (Phase 9).
- [ ] Back up `E:/Zenderal/Stock game`, `profiles/Ultra`, `ModOrganizer.ini` and
      `Zenderal.compiler_settings` to `E:/Zenderal-backups/`.
- [ ] In MO2, clone Ultra → **`Ultra AE`**, and create an empty-ish **`AE Bringup`** profile for Phase 1.
- [ ] Download every AE archive in Phase 2's table into MO2 (download only).
- [ ] Install the updated Enderal SE 2.1.4.4 via Steam (or the mod.pub installer). Read its
      `SkyrimSE.exe` version and write it here: `runtime = __________`

## Phase 1 — Game, SKSE, base (in the `AE Bringup` profile)

- [ ] Move the old `Stock game` out to `E:/Zenderal-backups/Stock game 1.5.97`, then build a new
      `Stock game` from the 2.1.4.4 install. Enderal's installer now bundles SKSE and Address Library;
      use the SKSE that comes with it.
- [ ] Check that `EnderalVersion.ini` reads 2.1.4.x, and that `EnderalSE.dll`, `fs_steam.dll`,
      `SkyrimRedirector.dll` and `YesImSure.dll` come from the new install. The old `SkyrimRedirector`
      and `YesImSure` were 1.5.97-only builds.
- [ ] Address Library for SKSE Plugins: already ships `versionlib-1-7-104-0.bin` (and 1.6.1179). Keep it.
- [ ] Engine Fixes (17230): install the AE main file plus the AE **part 2** preloader. That covers the
      `Engine Fixes - Preloader` mod *and* `Stock game/d3dx9_42.dll`. Read the page for 1.7 support
      first: Engine Fixes is the mod most tied to exact game versions.
- [ ] Get a crash logger in place before anything else: **.NET Script Framework has no AE build**.
      Install the Crash Logger SSE AE VR **DLL**. The list has only its PDB-support add-on today
      (`Crash Logger SSE AE VR - PDB support` holds just `SkyrimSE.pdb`, which is 1.5.97-specific; swap
      it for the new runtime's PDB or drop it). Disable `.NET Script Framework`.
- [ ] Launch to the main menu → check `skse64.log` shows the right runtime and no load errors.
- [ ] Disable **Backported Extended ESL Support (BEES)**. AE loads HEDR 1.71 plugins natively.

## Phase 2 — Swap every 1.5.97-only DLL (in `Ultra AE`)

For "same page" rows, the installed archive name shows it is the page's SE/1.5 file; take that page's
AE/NG file instead. Always read the page for **1.7.104** support. Where the page offers only an AE build
for 1.6.x, it still has to pass `skse64.log` on 1.7.

**Frameworks — install these first, launch, check the log:**

| Mod folder | Nexus | Installed | Swap to |
|---|---|---|---|
| JContainers SE | 16495 | 4.1.13 (2020) | same page, AE file |
| PapyrusUtil SE | 13048 | 3.9 (2020) | same page, AE file |
| powerofthree's Papyrus Extender | 22854 | 5.10.0 | same page, AE/NG file |
| powerofthree's Tweaks | 51073 | 1.16.0 | same page, AE/NG file |
| Spell Perk Item Distributor | 36869 | 7.3.2 | same page, AE/NG file |
| Keyword Item Distributor | 55728 | 4.0.6 | same page, AE/NG file |
| Base Object Swapper | 60805 | 3.5.0 | same page, AE/NG file |
| SkyPatcher | 106659 | 7.1.3 (“SE” archive) | same page, AE file |
| Custom Skills Framework | 41780 | 3.2.0 (“for 1.5.97”) | same page, AE main file (Prophecy needs it) |
| RaceMenu | 19080 | 0.4.16 (2020) | same page, AE file |
| Console Commands Extender | 28210 | 1.8.0 (2020) | same page, AE file |
| ConsolePlusPlus | 79975 | 1.5.0 | same page, AE/NG file |
| Cached Recursive Directory Walk | 186434 | 1.1.4 (“SE” archive) | same page, AE file; rebuild the cache after |

**Gameplay / UI:**

| Mod folder | Nexus | Installed | Swap to |
|---|---|---|---|
| SmoothCam | 41252 | 1.7.1 | same page, AE file; re-test CCC Stand Down |
| Frozen Electrocuted Combustion | 3532 | 6.1.1 | same page, AE/NG file |
| Security Overhaul SKSE - Lock Variations | 58224 | 4.0.0 | same page, AE/NG file |
| Simple Offence Suppression | 41764 | 2.3.0 | same page, AE/NG file |
| Dynamic Location Popups | 153122 | 1.0.1 | same page, AE/NG file |
| Photo Mode | 91701 | 3.0.4 | same page, AE/NG file |
| Better Jumping SE | 18967 | 1.7.3 | same page, AE file |
| Classic Sprinting Redone (SKSE64) | 20166 | 2.2 (2021) | same page, AE file |
| Stop On Slash AE | 66155 | 2.2 (“SSE” archive) | same page, AE file |
| Oxygen Meter 2 - Fixes and Additions | 171916 | 1.0.8 (“SE” archive) | same page, AE file |
| Horizon Fix SE | 184607 | 0.4.1 | same page, AE file if offered |
| Face Discoloration Fix | 42441 | 1.0.1 (2021) | same page, AE file |
| AddItemMenu | 17563 | 1.13 (2020) | check page for an AE build; else drop (debug tool) |
| Auto Input Switch | 54309 | 1.1.2 (2021) | check page for an AE build |
| Fix Note Icon for SkyUI | 32561 | 1.2.1 (2020) | check page; **re-evaluate**: Enderal 2.1.4.3 added SkyUI 6.0 support |
| Mfg Fix | 11669 | 1.5.4 (2020) | check page for an AE build; if none, **Mfg Fix NG** (separate page) and disable this |

**Disable — a 1.5 build sitting on top of an AE/NG build that's already installed:**

| Disable | Already installed underneath |
|---|---|
| Knotwork for Skyrim 1.5 (129164) | Knotwork (128235) 2.1.1 |
| MCM Helper for Skyrim 1.5 (192419) | MCM Helper (53000) 1.6.3 |
| Inventory Interface Information Injector for Skyrim 1.5 (87002) | Inventory Interface Information Injector Improved |
| Enderal Map Markers - CoMAP Patch (605): **hide only its `MapMarkerFramework.dll`**, keep its data | CoMAP (56123) 4.4, AE DLL |
| Loki's Wade In Water, dTry's Key Utils SE, OxygenMeter2 (already losing) | Wade In Water Redone, dTry Plugin Updates, Oxygen Meter 2 Fixes |

**AE-only DLLs that are dormant today and will start loading — decide each:**
- [ ] Beard Mask Fix (80232)
- [ ] Constructible Object Custom Keyword System (81409, `CraftingCategories.dll`)

## Phase 3 — The dual DLLs (~120 mods): let the log decide

- [ ] Enable everything in `Ultra AE`, launch, then go through every line of `skse64.log`. Any plugin
      reported as incompatible or failed goes into a table here and gets updated from its page (Nexus ID
      and installed version are in the inventory CSV).
- [ ] Enderal-specific forks need explicit checks, since a generic AE build won't replace them:
      wheeler-enderal-fix, Compass Navigation Overhaul - Enderal Patch, Hero Menu Enhanced,
      Biggie Traits - Enderal Conversion.
- [ ] Update any mod whose page has a newer 1.7 build even when it loads. CommonLib layout changes can
      crash at runtime without a load error.
- [ ] Re-check what Enderal 2.1 now does itself: QuickLoot integration (the QuickLoot patch is merged
      into Enderal), SkyUI 6.0, widescreen. List mods made redundant by it.

## Phase 4 — Our own DLLs (this repo)

- [ ] Update the repo-root `lib/` CommonLibSSE-NG to a build that supports 1.7.104, then rebuild all of:
      BlockReleaseFix, CrossbowDrawFix, CCCStandDown, DBVOPlayerLipSync, TrueHUDCombatIcons,
      GamepadCombos, DBVOSexDefaults. They hook through vtables/RelocationIDs, so they should port as is.
- [ ] **ChocolatePoiseEnderal**: `ZenCPRFactionFix.dll` and `ZenChocolatePoiseFix.dll` are .NET Script
      Framework plugins and die with it. Rewrite them as SKSE plugins, or check whether CPR's AE build
      still needs the fix.
- [ ] **ImprovedCameraSheatheFix**: it NOPs bytes inside IC 1.1.2.4228. Re-derive the patch site in the
      IC build that supports 1.7.
- [ ] **DBVOSexDefaults**: calls DBVO.dll `+0x2AC20`, pinned to DBVO 2.0.2.2. Re-derive it if DBVO
      updates.
- [ ] **GamepadCombos**: it exists because *1.5.97* ignores gamepad combo modifiers. Test whether 1.7
      still does before shipping it again.
- [ ] **PrecisionFork**: rebase onto the Precision release that supports 1.7, rebuild, re-test floating
      ice/crystal elementals.
- [ ] Re-cut the Patch Collection for AE (the 1.5 Patch Collection is prepped but not uploaded; decide
      whether it ever ships).

## Phase 5 — Enderal 2.1's content changes

- [ ] Re-serialize `reference/base/` (FS + base `Skyrim.esm`/`Update.esm`) from 2.1.4.4 and diff against
      the 2.0.12.4 trees. Keep the old trees under another name.
- [ ] Every Zenderal patch that overrides a changed record: rebuild from the new master (rule 5 —
      forward, don't revert). Check generated patches first: MagicPatches, PrettyArmoryEGO, FlintlockOverhaul,
      ReversalShadow, QuieterWaterfalls.
- [ ] Third-party Enderal mods built on 2.0.12.4 (EGO overrides 6203 records) will now **revert 2.1's
      fixes** wherever they touch a changed record. Run the diff against EGO's and the other big
      overhauls' YAML, and check each author for a 2.1 update.
- [ ] Extract the new `ScriptsEnderal.zip` → `papyrus-source/enderal`, diff, and re-fork every SureAI
      script we ship: FeverDeathLatchFix, BrawlFixes, ZenTraitsFixes, ControllerTweaks
      (`_00E_Game_SkillmenuSC`), FlameShot, KataFixes, SettingsApplier. Also check third-party
      script-only mods that overwrite `_00E_` scripts.
- [ ] Re-check the alchemy-touching mods and NpcPotions' SPID ini against the reworked alchemy.

## Phase 6 — Regenerate list-wide outputs

- [ ] TexGen + DynDOLOD (`TexGen Output - Zenderal`, `DynDOLOD Output - Zenderal`). Enderal 2.1 ships
      new LOD and changed records.
- [ ] Pandora (`Pandora Output - Zenderal`), with zpaired + zpairset ticked.
- [ ] CRDW cache, always after Pandora and installs.
- [ ] `magic-extract`; the SPID/KID logs (`Registered X/Y`).

## Phase 7 — Play-test (new game)

- [ ] New game → Skip The Prologue → Jespar's camp.
- [ ] Combat: Precision, MCO/FHR, TK Dodge, poise/parry, block release, crossbows/flintlocks.
- [ ] UI: MCMs (MCM Helper), Hero Menu, TrueHUD icons, QuickLoot, Wheeler, Compass, controller chords.
- [ ] Visuals: ENB, Theos, terrain, LOD.
- [ ] Force one crash and confirm Crash Logger writes a log; note its path.

## Phase 8 — Docs

- [ ] CLAUDE.md: the "SSE 1.5.97, not 1.6.x" rule, the HEDR 1.71/BEES rule, the .NET Script Framework
      crash-log trap. `arch-docs/enderal/install-and-engine.md`, `workspace/testing-and-debugging.md`.
- [ ] Patch docs whose fix assumed 1.5.97 (GamepadCombos, ImprovedCameraSheatheFix, ChocolatePoiseEnderal).

## Phase 9 — Compile and release

- [ ] Delete the backed-up 1.5 mod folders from `E:/Zenderal/mods`. Update `Zenderal.compiler_settings`
      (profile `Ultra AE`; drop Include rules for disabled mods).
- [ ] Wabbajack compile against the new Stock Game; test install into a clean folder.
- [ ] Release our rebuilt patches (`github-release`), then the list. Announce that 2.1 needs a new game.
