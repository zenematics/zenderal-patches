# Patches

One doc per folder in `src/`: what it ships, its FormID block, how it works and what it cost to learn. `CLAUDE.md` keeps a one-line row per patch; the detail lives here.

| Patch | Ships | Block |
|---|---|---|
| [`RelentlessSwordPatreon`](RelentlessSwordPatreon.md) | `Zenderal - Relentless Sword.esp` | `0x800–0x831` |
| [`MagicPatches`](MagicPatches.md) | `Zenderal - Magic Patches.esp` | _(none used)_ |
| [`KataFixes`](KataFixes.md) | `Zenderal - Kata Fixes.esp` | _(none used)_ |
| [`SkipPrologue`](SkipPrologue.md) | `Zenderal - Skip The Prologue.esp` | `0x800–0x802` |
| [`FasterSprint`](FasterSprint.md) | `Zenderal - Faster Sprint.esp` | none (overrides only) |
| [`QuieterWaterfalls`](QuieterWaterfalls.md) | `Zenderal - Quieter Waterfalls.esp` | none (overrides only) |
| [`DynamicDodgeNoSway`](DynamicDodgeNoSway.md) | **no plugin** (OAR files only) | none |
| [`DynamicDodgeShotFix`](DynamicDodgeShotFix.md) | `Zenderal - Dynamic Dodge Shot Fix.esp` | none (overrides only) |
| [`HalfStarlingDS`](HalfStarlingDS.md) | `Zenderal - Half Starling DS Races.esp` | none (overrides only) |
| [`RiverBush`](RiverBush.md) | `Zenderal - RiverBush.esp` | `0x800–0x81F` |
| [`SettingsApplier`](SettingsApplier.md) | `Zenderal - Settings Applier.esp` + `ZEN_SettingsApplier.pex` | `0x800` |
| [`FHRParryPoise`](FHRParryPoise.md) | `Zenderal - FHR Parry Poise.esp` | none (overrides only) |
| [`ChocolatePoiseEnderal`](ChocolatePoiseEnderal.md) | `Zenderal - Chocolate Poise Enderal Fix.esp` + `ZenCPRFactionFix.dll` (NSF) | `0x800–0x808` |
| [`BrawlFixes`](BrawlFixes.md) | *(no plugin — two recompiled scripts)* | _(none)_ |
| [`NpcPotions`](NpcPotions.md) | `Zenderal - NPC Potions_DISTR.ini` | _(none — SPID config, no plugin)_ |
| [`ControllerTweaks`](ControllerTweaks.md) | *(no plugin — three file overrides)* | _(none)_ |
| [`OldTempleWeather`](OldTempleWeather.md) | `Zenderal - Old Temple Weather.esp` | none (overrides only) |
| [`BakaHeroMenu`](BakaHeroMenu.md) | **RETIRED 2026-10-14**, was *(no plugin — `SKSE/Plugins/BakaHeroMenu.dll`)* | _(none)_ |
| [`TrueHUDCombatIcons`](TrueHUDCombatIcons.md) | *(no plugin — `SKSE/Plugins/ZenTrueHUDCombatIcons.dll` + configs)* | _(none)_ |
| [`FrostAtronachSEFix`](FrostAtronachSEFix.md) | *(no plugin — converted meshes, MO2 mod `Zenderal - Frost Atronach SE Fix`)* | _(none)_ |
| [`PrecisionLiftFix`](PrecisionLiftFix.md) | **RETIRED 2026-10-13**, was *(no plugin — converted `actors/atronachfrost/character assets/skeleton.nif` + diagnostic `SKSE/Plugins/ZenPrecisionLiftFix.dll`, MO2 mod `Zenderal - Precision Lift Fix`)* | _(none)_ |
| [`PrecisionFork`](PrecisionFork.md) | Reinstated 2026-10-16 *(rebuilt `Precision.dll` + `Precision_ZenderalFixes.ini`, MO2 mod `Zenderal - Precision Fork`, sorted directly ABOVE `Precision`)* | _(none)_ |
| [`ZenTraitsFixes`](ZenTraitsFixes.md) | *(no plugin — one recompiled script)* | _(none)_ |
| [`LearningBooks`](LearningBooks.md) | **RETIRED 2026-10-14**, was `Zenderal - Learning Books Grant Learning Points.esp` | `0x800–0x802` |
| [`MCODirectionalPowerAttacks`](MCODirectionalPowerAttacks.md) | `Zenderal - MCO Directional Power Attacks.esp` | none (overrides only) |
| [`PrettyArmoryEGO`](PrettyArmoryEGO.md) | `Zenderal - Pretty Armory EGO Patch.esp` | none (overrides only) |
| [`ArkMyradPlatformFix`](ArkMyradPlatformFix.md) | `Zenderal - Ark Myrad Platform Fix.esp` | none (overrides only) |
| [`ArkMarketTreeFix`](ArkMarketTreeFix.md) | `Zenderal - Ark Market Tree Fix.esp` | none (overrides only) |
| [`ArkBridgeOverhaulFixes`](ArkBridgeOverhaulFixes.md) | `Zenderal - Ark Bridge Overhaul Fixes.esp` | `0x800–0x817` |
| [`EppiRivervilleStatues`](EppiRivervilleStatues.md) | `Zenderal - EPPI Riverville Statues Patch.esp` | none (overrides only) |
| [`FeverDeathLatchFix`](FeverDeathLatchFix.md) | *(no plugin — one recompiled script)* | _(none)_ |
| [`UndeadCreaturesReplacerEGO`](UndeadCreaturesReplacerEGO.md) | `Zenderal - Undead Creatures Replacer EGO Patch.esp` | none (overrides only) |
| [`EnderalTextureRestores`](EnderalTextureRestores.md) | *(no plugin — loose textures, MO2 mod `Zenderal - Enderal Texture Restores`)* | _(none)_ |
| [`PrettyFemaleMeshRestores`](PrettyFemaleMeshRestores.md) | *(no plugin — loose meshes, MO2 mod `Zenderal - Pretty Female Mesh Restores`)* | _(none)_ |
| [`TerrainTextureSetFix`](TerrainTextureSetFix.md) | `Zenderal - Terrain Texture Set Fix.esp` | none (overrides only) |
| [`MissingParallaxHeights`](MissingParallaxHeights.md) | *(no plugin — loose textures, MO2 mod `Zenderal - Missing Parallax Heights`)* | _(none)_ |
| [`ArkWallCurbFix`](ArkWallCurbFix.md) | *(no plugin — Enderal's original meshes, MO2 mod `Zenderal - Ark Wall Curb Fix`)* | _(none)_ |
| [`ApocalypseNaviFix`](ApocalypseNaviFix.md) | *(HOTFIX — rebuilt `Apocalypse - Magic of Skyrim.esp`, MO2 mod `Zenderal - Apocalypse NAVI Fix`)* | _(none)_ |
| [`Prophecy`](Prophecy.md) | `Zenderal - Prophecy.esp` + 2 scripts + `NetScriptFramework/Plugins/CustomSkill.Prophecy.config.txt` | `0x800–0x807` |
| [`ImprovedCameraSheatheFix`](ImprovedCameraSheatheFix.md) | *(no plugin — `SKSE/Plugins/ZenICSheatheFix.dll`)* | _(none)_ |
| [`HorseCloakFluffFix`](HorseCloakFluffFix.md) | `Zenderal - Horse Cloak Fluff Fix.esp` + 2 generated meshes | none (overrides only) |
| [`DintHairs`](DintHairs.md) | *(rebuilt third-party plugins, MO2 mods `[Dint999] BDOR Hairs - Hairs Only` / `[Dint999] HairPack02 - Hairs Only`)* | _(none)_ |
| [`GuardFalconer`](GuardFalconer.md) | `Zenderal - Guard Falconer Patch.esp` | none (overrides only) |
| [`MoonsteelPretty`](MoonsteelPretty.md) | `Zenderal - Moonsteel Pretty Patch.esp` + 2 loose meshes | none (overrides only) |
| [`FlintlockOverhaul`](FlintlockOverhaul.md) | `Zenderal - Flintlock Overhaul.esp` + `ZP_FlintlockAmmoPlayerScript.pex` + `Zenderal - DAR Rifles Recipes Off.esp` + `_KID.ini` + Wheeler icons | `0x800–0x813` |
| [`DragonPriestStaffSwap`](DragonPriestStaffSwap.md) | *(no plugin — loose meshes, MO2 mod `Zenderal - Dragon Priest Staff Swap`)* | _(none)_ |
| [`StaffDrawFix`](StaffDrawFix.md) | *(no plugin — OAR submod, MO2 mod `Zenderal - Staff Draw Fix`)* | _(none)_ |
| [`LoopPistolAnims`](LoopPistolAnims.md) | *(no plugin — OAR mod, MO2 mod `Zenderal - Loop Pistol Animations`)* | _(none)_ |
| [`NoScreenFlashes`](NoScreenFlashes.md) | `Zenderal - No Screen Flashes.esp` | none (overrides only) |
| [`EnderalPairedAnims`](EnderalPairedAnims.md) | *(no plugin — Pandora-native patch `Pandora_Engine/mod/zpaired`, MO2 mod `Zenderal - Enderal Paired Animations`)* | _(none)_ |
| [`DBVOPlayerLipSync`](DBVOPlayerLipSync.md) | *(no plugin — `ZenDBVOLipSync.dll` + CCC `SD_user.ini`, MO2 mod `Zenderal - DBVO Player Lip Sync`)* | _(none)_ |
| [`CCCStandDown`](CCCStandDown.md) | *(no plugin — `ZenCCCStandDown.dll` + `.ini`, MO2 mod `Zenderal - CCC Stand Down`)* | _(none)_ |
| [`GamepadCombos`](GamepadCombos.md) | *(no plugin — `ZenGamepadCombos.dll` + `.ini`, MO2 mod `Zenderal - Gamepad Combos`)* | _(none)_ |
| [`Fuse00ArmorRaces`](Fuse00ArmorRaces.md) | `Zenderal - Fuse00 Armor Races.esp` | none (overrides only) |
| [`EGO21Compat`](EGO21Compat.md) | `Zenderal - EGO 2.1 Compatibility.esp` | none (overrides only) |
| [`GrassLightingFix`](GrassLightingFix.md) | *(generated meshes, `Zenderal - Grass Lighting Fix`)* | none |
| [`TextureRename21Fix`](TextureRename21Fix.md) | *(generated textures, `Zenderal - 2.1 Texture Rename Fix`)* | none |
| [`SuraClaymoreFix`](SuraClaymoreFix.md) | `Zenderal - Sura Claymore Fix.esp` | none (overrides only) |
| [`RaySensePriority`](RaySensePriority.md) | **no plugin** (OAR files only) | none |
| [`ReversalShadow`](ReversalShadow.md) | `Zenderal - Reversal Shadow.esp` + generated meshes/texture/sound | `0x800–0x808` |
| [`PerpetuumTheaterEVGATFix`](PerpetuumTheaterEVGATFix.md) | `Zenderal - Perpetuum Theater EVGAT Fix.esp` | none (overrides only) |
| [`EppiRivervilleCobbleRemoval`](EppiRivervilleCobbleRemoval.md) | `Zenderal - EPPI Riverville Cobble Removal.esp` | none (overrides only) |
| [`LastWatchTrapdoorFix`](LastWatchTrapdoorFix.md) | `Zenderal - Last Watch Trapdoor Fix.esp` | none (overrides only) |
| [`NoLightningFlash`](NoLightningFlash.md) | `Zenderal - No Lightning Flash.esp` | none (overrides only) |
| [`Levelsystem21Cleanup`](Levelsystem21Cleanup.md) | `Zenderal - 2.1 Levelsystem Cleanup.esp` | none (overrides only) |
| [`QyraIslandEditorIdFix`](QyraIslandEditorIdFix.md) | `Zenderal - Qyra Island EditorID Fix.esp` | none (overrides only) |
| [`UnresolvedRefsCleanup`](UnresolvedRefsCleanup.md) | `Zenderal - Unresolved References Cleanup.esp` | none (overrides only) |
| [`IronGolemClean`](IronGolemClean.md) | generated cleaned `mihailirongolem.esp` (not committed) | none |
| [`BiggieTraits171`](BiggieTraits171.md) | generated HEDR 1.71 `Biggie Traits.esp` (not committed) | none |
| [`KataAffinities21`](KataAffinities21.md) | `Zenderal - KataPUMB Affinities 2.1.esp` + `_00E_AffinityControl.pex` | none (one override) |
| [`LostOneSalletFix`](LostOneSalletFix.md) | *(generated mesh, not committed)* | none |
| [`LostOnesDismembering`](LostOnesDismembering.md) | `Zenderal - Lost Ones Dismembering.esp` + DF JSON + generated meshes | `0x800–0x832` |
| [`FrostSpiderMotherFix`](FrostSpiderMotherFix.md) | `Zenderal - Frost Spider Mother Fix.esp` | none (one override) |
| [`MaceSpeed`](MaceSpeed.md) | `Zenderal - Mace Speed.esp` | none (overrides only) |
| [`OldCemeteryCryptFix`](OldCemeteryCryptFix.md) | `Zenderal - Old Cemetery Crypt Fix.esp` | none (one override) |
| [`MusketHandling`](MusketHandling.md) | `ZenMusketHandling.dll` + `.ini` | none (no plugin) |
| [`ZarAhTextureFix`](ZarAhTextureFix.md) | *(copied textures, not committed)* | none |
| [`ArkGateSiegeFix`](ArkGateSiegeFix.md) | `Zenderal - Ark Gate Siege Fix.esp` + 2 scripts (**Enderal 2.0 release only**) | `0x800–0x801` |
| [`GroundCoverAlphaFix`](GroundCoverAlphaFix.md) | *(generated meshes, not committed)* | none |
| [`PusBeetleFixes`](PusBeetleFixes.md) | `Zenderal - Pus Beetle Fixes.esp` + generated skeleton | none (one override) |
| [`OCPASecondKey`](OCPASecondKey.md) | `ZenOCPASecondKey.dll` + ini | none (no plugin) |
| [`TraitsRework`](TraitsRework.md) | `Zenderal - Traits.esp` | `0x800–0x88F` (`0x800–0x843`, `0x870–0x878`, `0x880–0x881` used) |
| [`PerkOverhaul`](PerkOverhaul.md) | `Zenderal - Perk Overhaul.esp` + `ZEN_PO_BladeMasterCritHealSC.pex` | `0x800–0x8FF` (`0x800–0x801` used) |
| [`Goblins`](Goblins.md) | `Zenderal - Goblins.esp` + `.pex` + generated meshes; `Zenderal - Goblins Dismembering.esp` + DF JSON + generated meshes | `0x800–0xB29`; Dismembering `0x800–0x836` |
| [`EnemyDensity`](EnemyDensity.md) | `Zenderal - Enemy Density.esp`: 922 placed enemies in 187 groups (Fogville goblins/Arps, Whisperwood undead hordes, six more regions) | `0x800–0xD9B` |
| [`StancesNoIcon`](StancesNoIcon.md) | `Zenderal - Stances No Icon.esp` | none (overrides only) |
| [`KnightOfThePath`](KnightOfThePath.md) | `Zenderal - Knight of the Path.esp` + 25 meshes copied from ERA (not committed) | `0x800–0x813` |
| [`ReadTheRoomEnderal`](ReadTheRoomEnderal.md) | `Zenderal - Read the Room Enderal.esp` | none (one override) |
| [`BloodyCritSound`](BloodyCritSound.md) | `Zenderal - Bloody Crit Sound.esp` + 1 loose `.wav` (not committed) | none (one override) |
| [`LevelUpSound`](LevelUpSound.md) | `Zenderal - Level Up Sound.esp` + 1 loose `.wav` (not committed) | none (one override) |
| [`ZenKeyTrace`](ZenKeyTrace.md) | `ZenKeyTrace.dll` | none (no plugin) |
| [`CastingBarAE`](CastingBarAE.md) | `CastingBar.dll` (zax's Casting Bar rebuilt for 1.7.104) | none (no plugin) |
| [`AspectLayout`](AspectLayout.md) | `_ZenAspectLayout.dll` + ini; layout sets generated (not committed) | none (no plugin) |
| [`SilvergroveStoneWalls`](SilvergroveStoneWalls.md) | *(generated meshes + textures, not committed)* | none |
| [`SPRPBRTweaks`](SPRPBRTweaks.md) | *(generated PGPatcher JSONs, not committed)* | none |
| [`TerrainParallaxShadowDistance`](TerrainParallaxShadowDistance.md) | *(generated Bottled Shaders `.hlsli`, not committed)* | none |
| [`HighPolyDefaultHeads`](HighPolyDefaultHeads.md) | `Zenderal - High Poly Default Heads.esp` | none (18 overrides) |
| [`UnskippableCinematics`](UnskippableCinematics.md) | *(7 recompiled SureAI scripts)* | none (no plugin) |
| [`TestingCheats`](TestingCheats.md) | `Zenderal - Testing Cheats.esp` + 2 scripts | `0x800–0x804` |
| [`CallCompanions`](CallCompanions.md) | `Zenderal - Call Companions.esp` + 2 scripts | `0x800–0x803` |
| [`LostOneArcherAmmo`](LostOneArcherAmmo.md) | `Zenderal - Lost One Archer Ammo.esp` | none (overrides only) |
| [`SteaminTWoEWeatherList`](SteaminTWoEWeatherList.md) | *(generated `_weatherlist.ini`, not committed)* | none |
| [`CreatureRagdollFix`](CreatureRagdollFix.md) | Pandora patch `zragfix`, human `0_master` contact edit + draugr get-up matcher start event | none (no plugin) |
| [`ZenRagdollTrace`](ZenRagdollTrace.md) | Testing tool: SKSE logger of ragdoll/get-up graph events and state | none (no plugin) |
| [`AirborneGetUpFix`](AirborneGetUpFix.md) | `ZenAirborneGetUpFix.dll`: holds mid-air `GetUpBegin` until the ragdoll settles | none (no plugin) |
| [`DFSlowTimeGuard`](DFSlowTimeGuard.md) | `ZenDFSlowTimeGuard.dll`: stops DF's slow-mo reset cancelling Seismic Stomp's SlowTime | none (no plugin) |
| [`SkeletonRagdollFix`](SkeletonRagdollFix.md) | generated loose `skeletons.hkx`: skeleton ragdoll limbs bend | none (no plugin) |
| [`IEDPistolHolsters`](IEDPistolHolsters.md) | IED ExtraGearNodes file + generated IED export: pistols placed apart from staves | none (no plugin) |
