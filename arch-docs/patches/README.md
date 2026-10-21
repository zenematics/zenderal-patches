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
| [`KataAffinities21`](KataAffinities21.md) | `Zenderal - KataPUMB Affinities 2.1.esp` + `_00E_AffinityControl.pex` | none (one override) |
| [`LostOneSalletFix`](LostOneSalletFix.md) | *(generated mesh, not committed)* | none |
| [`LostOnesDismembering`](LostOnesDismembering.md) | `Zenderal - Lost Ones Dismembering.esp` + DF JSON + generated meshes | `0x800–0x832` |
| [`FrostSpiderMotherFix`](FrostSpiderMotherFix.md) | `Zenderal - Frost Spider Mother Fix.esp` | none (one override) |
| [`MaceSpeed`](MaceSpeed.md) | `Zenderal - Mace Speed.esp` | none (overrides only) |
| [`OldCemeteryCryptFix`](OldCemeteryCryptFix.md) | `Zenderal - Old Cemetery Crypt Fix.esp` | none (one override) |
| [`MusketHandling`](MusketHandling.md) | `ZenMusketHandling.dll` + `.ini` | none (no plugin) |
| [`Goblins`](Goblins.md) | `Zenderal - Goblins.esp` + `.pex` + generated meshes; `Zenderal - Goblins Dismembering.esp` + DF JSON + generated meshes | `0x800–0xB29`; Dismembering `0x800–0x836` |
