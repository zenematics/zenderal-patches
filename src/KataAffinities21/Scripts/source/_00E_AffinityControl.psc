Scriptname _00E_AffinityControl extends ReferenceAlias Conditional

; ATTENTION
; this script contains a new affinity system that requires FS. Therefore, many elements in this script are redundant, as
; one version is required for the new system and one is required so that the old system can be used when FS is not
; available. If possible, the properties and functions are labeled with NEW or OLD in comments

;=====================================================================================
 ;                                      EVENTS                                   
;=====================================================================================

Event OnInit()
    InitAffinitySystem()
EndEvent

Event OnPlayerLoadGame()
    InitAffinitySystem()
EndEvent


;=====================================================================================
;                                       FUNCTIONS                                    
;=====================================================================================

int function _GetScriptVersion() Global
    return 1
endFunction

Int Function RegisterPerkTree(int index, FormList perkTree, Message affinityName_Male, Message affinityName_Female)    
    PerkTree_Trees[index]                = perkTree
    PerkTree_AffinityNames_Male[index]   = affinityName_Male
    PerkTree_AffinityNames_Female[index] = affinityName_Female
    Return index
EndFunction

Int Function RegisterAffinity(int index, Spell affSpell, Message name_Male, Message name_Female)
    Affinity_Spells[index]       = affSpell
    Affinity_Names_Male[index]   = name_Male
    Affinity_Names_Female[index] = name_Female
    Return Index
EndFunction

Function InitAffinitySystem()

    BlockClassUpdates = True

    ; Perk trees
    PerkTree_Trees                = New FormList[12]
    PerkTree_AffinityNames_Male   = New Message[12]
    PerkTree_AffinityNames_Female = New Message[12]

    ; "no class" for GetPlayerClassName
    RegisterPerkTree( 0, None, _00E_Game_NoClassName, _00E_Game_NoClassName_Female)

    PerkTree_BastionIndex      = RegisterPerkTree( 1, BastionPerks, _00E_Game_BastionName, _00E_Game_BastionName_Female)
    PerkTree_DerwishIndex      = RegisterPerkTree( 2, DerwishPerks, _00E_Game_DerwishName, _00E_Game_DerwishName_Female)
    PerkTree_ElementalismIndex = RegisterPerkTree( 3, ElementalismPerks, _00E_Game_ElementalismName, _00E_Game_ElementalismName_Female)
    PerkTree_EspionageIndex    = RegisterPerkTree( 4, EspionagePerks, _00E_Game_EspionageName, _00E_Game_EspionageName_Female)
    PerkTree_LifeAndDeathIndex = RegisterPerkTree( 5, LifeAndDeathPerks, _00E_Game_LifeAndDeathName, _00E_Game_LifeAndDeathName_Female)
    PerkTree_ManipulationIndex = RegisterPerkTree( 6, ManipulationPerks, _00E_Game_ManipulationName, _00E_Game_ManipulationName_Female)
    PerkTree_RageIndex         = RegisterPerkTree( 7, RagePerks, _00E_Game_RageName, _00E_Game_RageName_Female)
    PerkTree_TrickeryIndex     = RegisterPerkTree( 8, TrickeryPerks, _00E_Game_TrickeryName, _00E_Game_TrickeryName_Female)
    PerkTree_VagabondIndex     = RegisterPerkTree( 9, VagabondPerks, _00E_Game_VagabondName, _00E_Game_VagabondName_Female)

	PerkTree_PhasmalistIndex      = RegisterPerkTree(10, FS_PhasmalistPerks, _00E_FS_Game_PhasmalistName, _00E_FS_Game_PhasmalistName_Female)
	PerkTree_TheriantrophistIndex = RegisterPerkTree(11, FS_TheriantrophistPerks, _00E_FS_Game_TheriantrophistName, _00E_FS_Game_TheriantrophistName_Female)

    ; Affinities
    Affinity_Spells       = New Spell[45]
    Affinity_Names_Male   = New Message[45]
    Affinity_Names_Female = New Message[45]

    Affinity_BattlemageIndex   = RegisterAffinity( 0, _00E_Affinity_AbBattlemage, _00E_Game_Affinity_BattlemageName, _00E_Game_Affinity_BattlemageName_Female)
    Affinity_ClericIndex       = RegisterAffinity( 1, _00E_Affinity_AbCleric, _00E_Game_Affinity_ClericName, _00E_Game_Affinity_ClericName_Female)
    Affinity_AssasinIndex      = RegisterAffinity( 2, _00E_Affinity_AbAssassin, _00E_Game_Affinity_AssassinName, _00E_Game_Affinity_AssassinName_Female)
    Affinity_WayfarerIndex     = RegisterAffinity( 3, _00E_Affinity_AbWayfarer, _00E_Game_Affinity_WayfarerName, _00E_Game_Affinity_WayfarerName_Female)
    Affinity_BlackMageIndex    = RegisterAffinity( 4, _00E_Affinity_AbBlackMage, _00E_Game_Affinity_BlackMageName, _00E_Game_Affinity_BlackMageName_Female)
    Affinity_DarkKeeperIndex   = RegisterAffinity( 5, _00E_Affinity_AbDarkKeeper, _00E_Game_Affinity_DarkKeeperName, _00E_Game_Affinity_DarkKeeperName_Female)
    Affinity_FencerIndex       = RegisterAffinity( 6, _00E_Affinity_AbFencer, _00E_Game_Affinity_BlademasterName, _00E_Game_Affinity_BlademasterName_Female)
    Affinity_BladebreakerIndex = RegisterAffinity( 7, _00E_Affinity_AbBladebreaker, _00E_Game_Affinity_BladebreakerName, _00E_Game_Affinity_BladebreakerName_Female)
    Affinity_ShadowdancerIndex = RegisterAffinity( 8, _00E_Affinity_AbShadowdancer, _00E_Game_Affinity_ShadowdancerName, _00E_Game_Affinity_ShadowdancerName_Female)
    Affinity_ArcaneArcherIndex = RegisterAffinity( 9, _00E_Affinity_AbArcaneArcher, _00E_Game_Affinity_ArcaneArcherName, _00E_Game_Affinity_ArcaneArcherName_Female)

    ; TODO: Wandering Mage
    Affinity_WanderingMageIndex = 10
    ; Affinity_WanderingMageIndex = RegisterAffinity(10, __Config_AffinityAbs[10], , )

	Affinity_SpectralistIndex       = RegisterAffinity(11, _00E_FS_Affinity_AbRitualist, _00E_FS_Game_Affinity_Spectralist, _00E_FS_Game_Affinity_Spectralist_Female)
	Affinity_GhostBladeIndex        = RegisterAffinity(12, _00E_FS_Affinity_AbGhostblade, _00E_FS_Game_Affinity_GhostBlade, _00E_FS_Game_Affinity_GhostBlade_Female)
	Affinity_SpectralWarriorIndex   = RegisterAffinity(13, _00E_FS_Affinity_AbSpectralWarrior, _00E_FS_Game_Affinity_SpectralWarrior, _00E_FS_Game_Affinity_SpectralWarrior_Female)
	Affinity_BruteIndex             = RegisterAffinity(14, _00E_FS_Affinity_AbBrute, _00E_FS_Game_Affinity_Brute, _00E_FS_Game_Affinity_Brute_Female)
	Affinity_DrifterIndex           = RegisterAffinity(15, _00E_FS_Affinity_AbDrifter, _00E_FS_Game_Affinity_Drifter, _00E_FS_Game_Affinity_Drifter_Female)
	Affinity_DruidIndex             = RegisterAffinity(16, _00E_FS_Affinity_AbDruid, _00E_FS_Game_Affinity_Druid, _00E_FS_Game_Affinity_Druid_Female)
	Affinity_NightwolfIndex         = RegisterAffinity(17, _00E_FS_Affinity_AbNightwolf, _00E_FS_Game_Affinity_Nightwolf, _00E_FS_Game_Affinity_Nightwolf_Female)
	Affinity_RavagerIndex           = RegisterAffinity(18, _00E_FS_Affinity_AbRavager, _00E_FS_Game_Affinity_Ravager, _00E_FS_Game_Affinity_Ravager_Female)
	Affinity_ScourgeOfTheWildsIndex = RegisterAffinity(19, _00E_FS_Affinity_AbScourge, _00E_FS_Game_Affinity_ScourgeOfTheWilds, _00E_FS_Game_Affinity_ScourgeOfTheWilds_Female)
	Affinity_SoulcallerIndex        = RegisterAffinity(20, _00E_FS_Affinity_AbSoulcaller, _00E_FS_Game_Affinity_Soulcaller, _00E_FS_Game_Affinity_Soulcaller_Female)

	;KATAPUMB NEW AFFINITIES (ported to 2.1 by Zenderal)

	Affinity_AcrobatIndex = RegisterAffinity(21, Kata_Affinity_AbAcrobat, Kata_Game_Affinity_Acrobat, Kata_Game_Affinity_Acrobat_Female)
	Affinity_BerserkerIndex = RegisterAffinity(22, Kata_Affinity_AbBerserker, Kata_Game_Affinity_Berserker, Kata_Game_Affinity_Berserker_Female)
	Affinity_DragonHunterIndex = RegisterAffinity(23, Kata_Affinity_AbDragonHunter, Kata_Game_Affinity_DragonHunter, Kata_Game_Affinity_DragonHunter_Female)
	Affinity_DuelistIndex = RegisterAffinity(24, Kata_Affinity_AbDuelist, Kata_Game_Affinity_Duelist, Kata_Game_Affinity_Duelist_Female)
	Affinity_KnightIndex = RegisterAffinity(25, Kata_Affinity_AbKnight, Kata_Game_Affinity_Knight, Kata_Game_Affinity_Knight_Female)
	Affinity_RiftMageIndex = RegisterAffinity(26, Kata_Affinity_AbRiftMage, Kata_Game_Affinity_RiftMage, Kata_Game_Affinity_RiftMage_Female)
	Affinity_SlayerIndex = RegisterAffinity(27, Kata_Affinity_AbSlayer, Kata_Game_Affinity_Slayer, Kata_Game_Affinity_Slayer_Female)
	Affinity_SpellSwordIndex = RegisterAffinity(28, Kata_Affinity_AbSpellSword, Kata_Game_Affinity_SpellSword, Kata_Game_Affinity_SpellSword_Female)
	Affinity_ThiefIndex = RegisterAffinity(29, Kata_Affinity_AbThief, Kata_Game_Affinity_Thief, Kata_Game_Affinity_Thief_Female)
	Affinity_WandererIndex = RegisterAffinity(30, Kata_Affinity_AbWanderer, Kata_Game_Affinity_Wanderer, Kata_Game_Affinity_Wanderer_Female)
	Affinity_WhiteMageIndex = RegisterAffinity(31, Kata_Affinity_AbWhiteMage, Kata_Game_Affinity_WhiteMage, Kata_Game_Affinity_WhiteMage_Female)

	;1.3 Version
	Affinity_BardIndex = RegisterAffinity(32, Kata_Affinity_AbBard, Kata_Game_Affinity_Bard, Kata_Game_Affinity_Bard_Female)
	Affinity_EnchanterIndex = RegisterAffinity(33, Kata_Affinity_AbEnchanter, Kata_Game_Affinity_Enchanter, Kata_Game_Affinity_Enchanter_Female)
	Affinity_ShadowCasterIndex = RegisterAffinity(34, Kata_Affinity_AbShadowCaster, Kata_Game_Affinity_ShadowCaster, Kata_Game_Affinity_ShadowCaster_Female)

	;2.0 Version
	Affinity_IndexCustodio = RegisterAffinity(35, Kata_V2_Affinity_AbCustodio, Kata_V2_Game_Affinity_Custodio, Kata_V2_Game_Affinity_Custodio_Female)
	Affinity_IndexHighlander = RegisterAffinity(36, Kata_V2_Affinity_AbHighlander, Kata_V2_Game_Affinity_Highlander, Kata_V2_Game_Affinity_Highlander_Female)
	Affinity_IndexLunatic = RegisterAffinity(37, Kata_V2_Affinity_AbLunatic, Kata_V2_Game_Affinity_Lunatic, Kata_V2_Game_Affinity_Lunatic_Female)
	Affinity_IndexMercenary = RegisterAffinity(38, Kata_V2_Affinity_AbMercenary, Kata_V2_Game_Affinity_Mercenary, Kata_V2_Game_Affinity_Mercenary_Female)
	Affinity_IndexMonk = RegisterAffinity(39, Kata_V2_Affinity_AbMonk, Kata_V2_Game_Affinity_Monk, Kata_V2_Game_Affinity_Monk_Female)
	Affinity_IndexPackLeader = RegisterAffinity(40, Kata_V2_Affinity_AbPackLeader, Kata_V2_Game_Affinity_PackLeader, Kata_V2_Game_Affinity_PackLeader_Female)
	Affinity_IndexPoisoner = RegisterAffinity(41, Kata_V2_Affinity_AbPoisoner, Kata_V2_Game_Affinity_Poisoner, Kata_V2_Game_Affinity_Poisoner_Female)
	Affinity_IndexSoulReaper = RegisterAffinity(42, Kata_V2_Affinity_AbSoulReaper, Kata_V2_Game_Affinity_SoulReaper, Kata_V2_Game_Affinity_SoulReaper_Female)
	Affinity_IndexWitcher = RegisterAffinity(43, Kata_V2_Affinity_AbWitcher, Kata_V2_Game_Affinity_Witcher, Kata_V2_Game_Affinity_Witcher_Female)
	Affinity_IndexWolfHunter = RegisterAffinity(44, Kata_V2_Affinity_AbWolfHunter, Kata_V2_Game_Affinity_WolfHunter, Kata_V2_Game_Affinity_WolfHunter_Female)
	;END KATAPUMB


    ; Init affinitiesUnlocked if necessary
    If affinitiesUnlocked.Length != Affinity_Spells.Length
        bool[] oldAffinities = affinitiesUnlocked as bool[] ; to really copy the array and not just copy the reference
        ResetUnlockedAffinities()

        Int Index = 0
        While Index < oldAffinities.Length && Index < affinitiesUnlocked.Length
            affinitiesUnlocked[Index] = oldAffinities[Index]
            Index += 1
        EndWhile
    EndIf

    ; Init MajorSchool
    If MajorSchool == 0
        UpdateMajorSchool()
    EndIf

    BlockClassUpdates = False

EndFunction

Function UpdateMajorSchool()

    ; Mage
    If MajorClassIndex == PerkTree_ElementalismIndex || MajorClassIndex == PerkTree_LifeAndDeathIndex || MajorClassIndex == PerkTree_ManipulationIndex || MajorClassIndex == PerkTree_PhasmalistIndex
        MajorSchool = 2

    ; Thief
    ElseIf MajorClassIndex == PerkTree_TrickeryIndex || MajorClassIndex == PerkTree_EspionageIndex || MajorClassIndex == PerkTree_VagabondIndex
        MajorSchool = 3

    ; Warrior
    Else
        MajorSchool = 1

    EndIf
EndFunction

Int[] Function GetPerkDistribution()
    Int[] PerkDistribution
	
	if SKSE.GetVersion() > 0
		PerkDistribution = Utility.CreateIntArray(PerkTree_Trees.Length, 0)
	else
		PerkDistribution = new int[12]
	endif
	
    Int Index = 0
    While Index < PerkTree_Trees.Length
        If PerkTree_Trees[Index]
            PerkDistribution[Index] = _00E_Func_GetPointsInClass.Run(PerkTree_Trees[Index])
        EndIf
        Index += 1
    EndWhile

    Return PerkDistribution
EndFunction

Int[] Function GetMaxPerkDistribution()
    Int[] MaxPerkDistribution

	if SKSE.GetVersion() > 0
		MaxPerkDistribution = Utility.CreateIntArray(PerkTree_Trees.Length, 0)
	else
		MaxPerkDistribution = new int[12]
	endif
	
    Int Index = 0
    While Index < PerkTree_Trees.Length
        If PerkTree_Trees[Index]
            MaxPerkDistribution[Index] = PerkTree_Trees[Index].GetSize()
        EndIf
        Index += 1
    EndWhile

    Return MaxPerkDistribution
EndFunction

Function UpdateClassIndices(Int[] PerkDistribution)
    Int Index

    ; Update major class/perk tree
    If MajorClassIndex > 0 && PerkDistribution[MajorClassIndex] == 0
        MajorClassIndex = 0
    EndIf

    Index = 1
    While Index < PerkDistribution.Length
        If PerkDistribution[Index] > PerkDistribution[MajorClassIndex]
            MajorClassIndex = Index
        EndIf
        Index += 1
    EndWhile

    UpdateMajorSchool()
	_00E_MajorClassIndex.SetValue(MajorClassIndex)

    ; Update minor class/perk tree
    If MinorClassIndex > 0 && (MinorClassIndex == MajorClassIndex || PerkDistribution[MinorClassIndex] == 0)
        MinorClassIndex = 0
    EndIf

    Index = 1
    While Index < PerkDistribution.Length
        If Index != MajorClassIndex && PerkDistribution[Index] > PerkDistribution[MinorClassIndex]
            MinorClassIndex = Index
        EndIf
        Index += 1
    EndWhile

	_00E_MinorClassIndex.SetValue(MinorClassIndex)

EndFunction

Function ResetUnlockedAffinities()
	if SKSE.GetVersion() == 0
		affinitiesUnlocked = new bool[45]
		return
	endif

    affinitiesUnlocked = Utility.CreateBoolArray(Affinity_Spells.Length, False)

    ; For whatever reason, the second "filler" arg in CreateBoolArray does not work, the array is filled with True
    ; So fill it with False by hand
    Int Index = 0
    While Index < affinitiesUnlocked.Length
        affinitiesUnlocked[Index] = False
        Index += 1
    EndWhile
EndFunction

Function TryUnlockAffinity(Int[] PerkDistribution, Int iAffinity, int iMainPerk, int iSecondaryPerk1, int iSecondaryPerk2 = 0, int iSecondaryPerk3 = 0)
    If PerkDistribution[iMainPerk] >= 10 && Affinity_Spells[iAffinity]
        If PerkDistribution[iSecondaryPerk1] >= 10 || PerkDistribution[iSecondaryPerk2] >= 10 || PerkDistribution[iSecondaryPerk3] >= 10
            affinitiesUnlocked[iAffinity] = True
        EndIf
    EndIf
EndFunction

Function UpdateUnlockedAffinities(Int[] PerkDistribution)
    ResetUnlockedAffinities()

    ; Battlemage: Elementarism + Derwish/Rage/Bastion
    TryUnlockAffinity(PerkDistribution, Affinity_BattlemageIndex, PerkTree_ElementalismIndex, PerkTree_DerwishIndex, PerkTree_RageIndex, PerkTree_BastionIndex)

    ; Cleric: Manipulation + Bastion/Rage
    TryUnlockAffinity(PerkDistribution, Affinity_ClericIndex, PerkTree_ManipulationIndex, PerkTree_BastionIndex, PerkTree_RageIndex)

    ; Assassin/Assassine: Infiltraor und Klingentänzer
    TryUnlockAffinity(PerkDistribution, Affinity_AssasinIndex, PerkTree_EspionageIndex, PerkTree_DerwishIndex)

    ; Wayfarer/Vielgereister: Vagabund und Gauner
    TryUnlockAffinity(PerkDistribution, Affinity_WayfarerIndex, PerkTree_VagabondIndex, PerkTree_TrickeryIndex)

    ; Black Mage/Schwarzmagier: Entropie und Elementarismus
    TryUnlockAffinity(PerkDistribution, Affinity_BlackMageIndex, PerkTree_LifeAndDeathIndex, PerkTree_ElementalismIndex)

    ; Black Keeper/Schwarzer Hüter: Sinistra und Bastion
    TryUnlockAffinity(PerkDistribution, Affinity_DarkKeeperIndex, PerkTree_LifeAndDeathIndex, PerkTree_BastionIndex)

    ; Fencer/Fechtmeister: Klingentänzer und Vandale
    TryUnlockAffinity(PerkDistribution, Affinity_FencerIndex, PerkTree_DerwishIndex, PerkTree_RageIndex)

    ; Bladebreaker/Klingenbrecher:  Klingentänzer/Bastion
    TryUnlockAffinity(PerkDistribution, Affinity_BladebreakerIndex, PerkTree_DerwishIndex, PerkTree_BastionIndex)

    ; Shadow Dancer/Schattentänzer:  Infiltator und Sinistra/Thaumaturg
    TryUnlockAffinity(PerkDistribution, Affinity_ShadowdancerIndex, PerkTree_EspionageIndex, PerkTree_LifeAndDeathIndex)

    ; Wandering Mage/Wandermagier: Vagabund und Thaumaturg/Elementarist (currently not implemented)
    TryUnlockAffinity(PerkDistribution, Affinity_WanderingMageIndex, PerkTree_VagabondIndex, PerkTree_ElementalismIndex, PerkTree_ManipulationIndex)

    ; Arcane Archer/Arkaner Schütze: Gauner und Thaumaturg/Elementarist/Sinistra
    TryUnlockAffinity(PerkDistribution, Affinity_ArcaneArcherIndex, PerkTree_TrickeryIndex, PerkTree_ElementalismIndex, PerkTree_ManipulationIndex, PerkTree_LifeAndDeathIndex)

    ; Ritualist (Spectralist): Sinistrop und Phasmalist
    TryUnlockAffinity(PerkDistribution, Affinity_SpectralistIndex, PerkTree_PhasmalistIndex, PerkTree_LifeAndDeathIndex)

    ; Spectral Warrior: Phasmalist und Vandale/Hüter/Klingentänzer
    TryUnlockAffinity(PerkDistribution, Affinity_SpectralWarriorIndex, PerkTree_PhasmalistIndex, PerkTree_RageIndex, PerkTree_BastionIndex, PerkTree_DerwishIndex)
    
    ; Ghostblade: Phasmalist und Infiltrator/Gauner
    TryUnlockAffinity(PerkDistribution, Affinity_GhostBladeIndex, PerkTree_PhasmalistIndex, PerkTree_EspionageIndex, PerkTree_TrickeryIndex)
    
    ; Brute: Vandal/Bladedancer und Lycantrophe
    TryUnlockAffinity(PerkDistribution, Affinity_BruteIndex, PerkTree_TheriantrophistIndex, PerkTree_DerwishIndex, PerkTree_RageIndex)

    ; Drifter: Vagrant und Lycantrophe
    TryUnlockAffinity(PerkDistribution, Affinity_DrifterIndex, PerkTree_TheriantrophistIndex, PerkTree_VagabondIndex)

    ; Druid: Lycantrophe und Elementarist
    TryUnlockAffinity(PerkDistribution, Affinity_DruidIndex, PerkTree_TheriantrophistIndex, PerkTree_ElementalismIndex)

    ; Nightwolf: Infiltrator und Lycantrophe
    TryUnlockAffinity(PerkDistribution, Affinity_NightwolfIndex, PerkTree_TheriantrophistIndex, PerkTree_EspionageIndex)

    ; Ravager: Sinistrope und Lycantrophe
    TryUnlockAffinity(PerkDistribution, Affinity_RavagerIndex, PerkTree_TheriantrophistIndex, PerkTree_LifeAndDeathIndex)

    ; Scourge of the Wilds: Keeper/Thaumaturgy und Lycantrophe
    TryUnlockAffinity(PerkDistribution, Affinity_ScourgeOfTheWildsIndex, PerkTree_TheriantrophistIndex, PerkTree_ManipulationIndex)

    ; Soulcaller: Phasmalist und Lycantrophe
    TryUnlockAffinity(PerkDistribution, Affinity_SoulcallerIndex, PerkTree_TheriantrophistIndex, PerkTree_PhasmalistIndex)

	;KATAPUMB NEW AFFINITIES (ported to 2.1 by Zenderal)
	
	;Acrobat: Trickster + Blade Dancer
	TryUnlockAffinity(PerkDistribution, Affinity_AcrobatIndex, PerkTree_TrickeryIndex, PerkTree_DerwishIndex)
	
	;Berserker: Vandal + Vagabund
	TryUnlockAffinity(PerkDistribution, Affinity_BerserkerIndex, PerkTree_RageIndex, PerkTree_VagabondIndex)
	
	;DragonHunter: Keeper + Trickster
	TryUnlockAffinity(PerkDistribution, Affinity_DragonHunterIndex, PerkTree_BastionIndex, PerkTree_TrickeryIndex)
	
	;Duelist: Vagabund + Bladedancer
	TryUnlockAffinity(PerkDistribution, Affinity_DuelistIndex, PerkTree_DerwishIndex, PerkTree_VagabondIndex)
	
	;Lord: Keeper + Vandal
	TryUnlockAffinity(PerkDistribution, Affinity_KnightIndex, PerkTree_BastionIndex, PerkTree_RageIndex)
	
	;RiftMage: Sinistra + Thaumaturge
	TryUnlockAffinity(PerkDistribution, Affinity_RiftMageIndex, PerkTree_LifeAndDeathIndex, PerkTree_ManipulationIndex)
	
	;Slayer: Infiltrator+Vandal
	TryUnlockAffinity(PerkDistribution, Affinity_SlayerIndex, PerkTree_EspionageIndex, PerkTree_RageIndex)

	;Spell Sword: Blade Dancer + Elementalism/Thaumaturg/Sinistra
	TryUnlockAffinity(PerkDistribution, Affinity_SpellSwordIndex, PerkTree_DerwishIndex, PerkTree_ElementalismIndex, PerkTree_LifeAndDeathIndex, PerkTree_ManipulationIndex)

	;Thief: Infiltator + Trickster
	TryUnlockAffinity(PerkDistribution, Affinity_ThiefIndex,  PerkTree_EspionageIndex, PerkTree_TrickeryIndex)
	
	;Wanderer: Vagabund + Thaumaturg/Elementarist/Sinistra
	TryUnlockAffinity(PerkDistribution, Affinity_WandererIndex, PerkTree_VagabondIndex, PerkTree_ElementalismIndex, PerkTree_LifeAndDeathIndex, PerkTree_ManipulationIndex)
	
	;White Mage: Elementalism + Thaumaturge
	TryUnlockAffinity(PerkDistribution, Affinity_WhiteMageIndex, PerkTree_ElementalismIndex, PerkTree_ManipulationIndex)
	
	;Version 1.3
	;Bard: Vagabund + Phasmalist
	TryUnlockAffinity(PerkDistribution, Affinity_BardIndex, PerkTree_VagabondIndex, PerkTree_PhasmalistIndex)
	
	;Enchanter: Phasmalist + Elementalism/Thaumaturg
	TryUnlockAffinity(PerkDistribution, Affinity_EnchanterIndex, PerkTree_PhasmalistIndex, PerkTree_ElementalismIndex, PerkTree_ManipulationIndex)
	
	;ShadowCaster: Elementalism + Infiltator
	TryUnlockAffinity(PerkDistribution, Affinity_ShadowCasterIndex, PerkTree_ElementalismIndex, PerkTree_EspionageIndex)
	
	
	;Version 2.0
	;Custodio: Keeper+Phasmalist
	TryUnlockAffinity(PerkDistribution, Affinity_IndexCustodio, PerkTree_PhasmalistIndex, PerkTree_BastionIndex)
	
	;HighLander: Vandal + Trickster
	TryUnlockAffinity(PerkDistribution, Affinity_IndexHighlander, PerkTree_RageIndex, PerkTree_TrickeryIndex)
	
	;Lunatic: Vandal + Lycantrophe
	TryUnlockAffinity(PerkDistribution, Affinity_IndexLunatic, PerkTree_RageIndex, PerkTree_TheriantrophistIndex)
	
	;Merc: Keeper + Infiltator
	TryUnlockAffinity(PerkDistribution, Affinity_IndexMercenary, PerkTree_BastionIndex, PerkTree_EspionageIndex)
	
	;Monk: Infiltrator + Thaumaturg
	TryUnlockAffinity(PerkDistribution, Affinity_IndexMonk, PerkTree_EspionageIndex, PerkTree_ManipulationIndex)
	
	;Pack Leader: Keeper + Lycantrophe
	TryUnlockAffinity(PerkDistribution, Affinity_IndexPackLeader, PerkTree_BastionIndex, PerkTree_TheriantrophistIndex)

	;Poisoner: Infiltator + Vagrant
	TryUnlockAffinity(PerkDistribution, Affinity_IndexPoisoner, PerkTree_EspionageIndex, PerkTree_VagabondIndex)
	
	;Soul Reaper: Vandal + Sinistrope
	TryUnlockAffinity(PerkDistribution, Affinity_IndexSoulReaper, PerkTree_RageIndex, PerkTree_LifeAndDeathIndex)

	;Witcher: Vagrant + Keeper
	TryUnlockAffinity(PerkDistribution, Affinity_IndexWitcher, PerkTree_VagabondIndex, PerkTree_BastionIndex)

	;Wolf Hunter: Trickster + Lycantrophe
	TryUnlockAffinity(PerkDistribution, Affinity_IndexWolfHunter, PerkTree_TrickeryIndex, PerkTree_TheriantrophistIndex)
	
	;END KATAPUMB

Endfunction

Function AddAchievementForAffinityUnlock(int nTotalUnlockedAffinityCount)

	If nTotalUnlockedAffinityCount >= 1
		Steam.UnlockAchievement("END_AFFINITY_01")
	EndIf
	If nTotalUnlockedAffinityCount >= 2
		Steam.UnlockAchievement("END_AFFINITY_02")
	EndIf

EndFunction

Function AddAchievementForFullMemoryTree(Int[] PerkDistribution, Int[] MaxPerkDistribution)

    Int Index = 1
    While Index < PerkDistribution.Length
        If PerkDistribution[Index] == MaxPerkDistribution[Index] && !bMemoryTreeAchievementUnlocked
            Steam.UnlockAchievement("END_MEMORY_TREE_01")
            bMemoryTreeAchievementUnlocked = true
        EndIf
        Index += 1
    EndWhile

EndFunction

Function GetPlayerClass()

    ; Wait for InitAffinitySystem to finish its job
    While BlockClassUpdates
        Utility.Wait(0.5)
    EndWhile

    Int[] PerkDistribution = GetPerkDistribution()

    UpdateClassIndices(PerkDistribution)
    
    If !bMemoryTreeAchievementUnlocked
        Int[] MaxPerkDistribution = GetMaxPerkDistribution()
        AddAchievementForFullMemoryTree(PerkDistribution, MaxPerkDistribution)
    EndIf

    ; What affinities are unlocked?
    Int iNewAffinityIndex = -1

    bool[] oldAffinities = affinitiesUnlocked as bool[] ; to really copy the array and not just copy the reference
    UpdateUnlockedAffinities(PerkDistribution)

    Int nTotalUnlockedAffinityCount = 0
    Int nSinceLastTimeUnlockedAffinityCount = 0
	
    Int[] unlockedAffinityIndices

	if SKSE.GetVersion() > 0
		unlockedAffinityIndices = Utility.CreateIntArray(affinitiesUnlocked.Length, 0)
	else
		unlockedAffinityIndices = new int[45]
	endif

    Int Index = 0
    While Index < affinitiesUnlocked.Length
        If affinitiesUnlocked[Index]
            If oldAffinities[Index] == False
                nSinceLastTimeUnlockedAffinityCount += 1
            EndIf
            unlockedAffinityIndices[nTotalUnlockedAffinityCount] = Index
            nTotalUnlockedAffinityCount += 1
        EndIf
        Index += 1
    EndWhile
    
    AddAchievementForAffinityUnlock(nTotalUnlockedAffinityCount)

    If nTotalUnlockedAffinityCount == 1
        iNewAffinityIndex = unlockedAffinityIndices[0]
    ElseIf nTotalUnlockedAffinityCount > 1

        ; Additional safeguard, in case something has been changed in the code, for example, affinity conditions
        Int iOldAffinity = iCurrentAffinityIndex
        If iOldAffinity >= 0 && affinitiesUnlocked[iOldAffinity] == False
            iOldAffinity = -1
        EndIf

        ; Don't ask
        If (bDontShowAffinityMessageAgain || nSinceLastTimeUnlockedAffinityCount == 0) && iOldAffinity >= 0
            iNewAffinityIndex = iOldAffinity

        ; FS ask
        Else
            iNewAffinityIndex = AskForAffinityFS(unlockedAffinityIndices, nTotalUnlockedAffinityCount, iOldAffinity)
        EndIf
    EndIf

    ; Set chosen affinity
    If iNewAffinityIndex != iCurrentAffinityIndex
        If iCurrentAffinityIndex >= 0
            PlayerREF.RemoveSpell(Affinity_Spells[iCurrentAffinityIndex])
        EndIf

        iCurrentAffinityIndex = iNewAffinityIndex

        If iCurrentAffinityIndex >= 0
            PlayerREF.AddSpell(Affinity_Spells[iCurrentAffinityIndex])
            ; Debug.Notification("Affinity unlocked!")
            _00E_Game_sUnlockedAffinity.Show()
            UIQuestCompleteM.Play(PlayerREF)
            _00E_EPHandler.GiveEP(450)
            NQ31.SetCurrentStageID(10)
        EndIf
    EndIf

Endfunction

Int Function AskForAffinityFS(Int[] unlockedAffinityIndices, Int nUnlockedAffinities, Int iOldAffinity)
    Bool enableDoNotShowAgain = False

    if iOldAffinity >= 0
        _00E_Affinity_Message_Actor_01.SetName(GetAffinityName(iOldAffinity))
        int button = _00E_Affinity_MessageboxNew.show()
        If button == 0
            bDontShowAffinityMessageAgain = True
            Return iOldAffinity
        EndIf

        enableDoNotShowAgain = True
    Else
        _00E_Affinity_MessageboxFirstAffinity.show()
    Endif

    UIListMenu menu = UIExtensions.GetMenu("UIListMenu") as UIListMenu
    
    int Index = 0    
    while Index < nUnlockedAffinities
        Int iAffinity = unlockedAffinityIndices[Index]
        menu.AddEntryItem(GetAffinityName(iAffinity), -1, iAffinity, False)
        Index += 1
    Endwhile
    
    if enableDoNotShowAgain
        menu.AddEntryItem(_00E_Affinity_DoNotShowAgain.getName(), -1, nUnlockedAffinities, False)
    Endif
    
    int choice = -1
    if UIExtensions.openMenu("UIListMenu")
        choice = menu.getResultInt()
    Endif

    if choice >= nUnlockedAffinities
        ; do not show again
        bDontShowAffinityMessageAgain = True
        Return iOldAffinity
    ElseIf choice < 0
        Return iOldAffinity
    Else
        Return unlockedAffinityIndices[choice]
    Endif
    
Endfunction

String Function GetGenderName(Int index, Message[] maleNames, Message[] femaleNames)
    if Player.GetSex() == 1
        Return femaleNames[index].GetName()
    Else
        Return maleNames[index].GetName()
    EndIf
EndFunction

String Function GetAffinityName(Int index)
    Return GetGenderName(index, Affinity_Names_Male, Affinity_Names_Female)
EndFunction

String Function GetPlayerClassName()
    If iCurrentAffinityIndex >= 0
        Return GetAffinityName(iCurrentAffinityIndex)
    Else
        String result = GetGenderName(MajorClassIndex, PerkTree_AffinityNames_Male, PerkTree_AffinityNames_Female)
        If MinorClassIndex > 0
            result += " / " + GetGenderName(MinorClassIndex, PerkTree_AffinityNames_Male, PerkTree_AffinityNames_Female)
        EndIf
        Return result
    EndIf
EndFunction


;=====================================================================================
;                                       PROPERTIES                                   
;=====================================================================================

int Property MajorClassIndex Auto Hidden
int Property MinorClassIndex Auto Hidden
int Property MajorSchool Auto
{ 1: Warrior; 2: Mage; 3: Thief }

int iCurrentAffinityIndex = -1
bool[] affinitiesUnlocked
bool bDontShowAffinityMessageAgain
bool bMemoryTreeAchievementUnlocked = False

ActorBase Property Player Auto
Actor Property PlayerREF Auto

ActorBase Property _00E_Affinity_Message_Actor_01 Auto
ActorBase Property _00E_Affinity_Message_Actor_02 Auto

Message Property _00E_Game_sUnlockedAffinity Auto

; name messages
Message Property _00E_Game_Affinity_BattlemageName Auto
Message Property _00E_Game_Affinity_ClericName Auto
Message Property _00E_Game_Affinity_AssassinName Auto
Message Property _00E_Game_Affinity_WayfarerName Auto
Message Property _00E_Game_Affinity_BlackMageName Auto
Message Property _00E_Game_Affinity_DarkKeeperName Auto
Message Property _00E_Game_Affinity_BlademasterName Auto
Message Property _00E_Game_Affinity_BladebreakerName Auto
Message Property _00E_Game_Affinity_ShadowdancerName Auto
Message Property _00E_Game_Affinity_ArcaneArcherName Auto

Message Property _00E_Game_Affinity_BattlemageName_Female Auto
Message Property _00E_Game_Affinity_ClericName_Female Auto
Message Property _00E_Game_Affinity_AssassinName_Female Auto
Message Property _00E_Game_Affinity_WayfarerName_Female Auto
Message Property _00E_Game_Affinity_BlackMageName_Female Auto
Message Property _00E_Game_Affinity_DarkKeeperName_Female Auto
Message Property _00E_Game_Affinity_BlademasterName_Female Auto
Message Property _00E_Game_Affinity_BladebreakerName_Female Auto
Message Property _00E_Game_Affinity_ShadowdancerName_Female Auto
Message Property _00E_Game_Affinity_ArcaneArcherName_Female Auto

Message Property _00E_Game_NoClassName_Female Auto
Message Property _00E_Game_BastionName_Female Auto
Message Property _00E_Game_DerwishName_Female Auto
Message Property _00E_Game_ElementalismName_Female Auto
Message Property _00E_Game_EspionageName_Female Auto
Message Property _00E_Game_LifeAndDeathName_Female Auto
Message Property _00E_Game_ManipulationName_Female Auto
Message Property _00E_Game_RageName_Female Auto
Message Property _00E_Game_TrickeryName_Female Auto
Message Property _00E_Game_VagabondName_Female Auto

Message Property _00E_Game_NoClassName Auto
Message Property _00E_Game_BastionName Auto
Message Property _00E_Game_DerwishName Auto
Message Property _00E_Game_ElementalismName Auto
Message Property _00E_Game_EspionageName Auto
Message Property _00E_Game_LifeAndDeathName Auto
Message Property _00E_Game_ManipulationName Auto
Message Property _00E_Game_RageName Auto
Message Property _00E_Game_TrickeryName Auto
Message Property _00E_Game_VagabondName Auto
;end name messages

Message Property _00E_Affinity_MessageboxNew Auto
Message Property _00E_Affinity_MessageboxFirstAffinity Auto
Message Property _00E_Affinity_DoNotShowAgain Auto

Spell Property _00E_Affinity_AbBattlemage Auto
Spell Property _00E_Affinity_AbCleric Auto
Spell Property _00E_Affinity_AbAssassin Auto
Spell Property _00E_Affinity_AbWayfarer Auto
Spell Property _00E_Affinity_AbBlackMage Auto
Spell Property _00E_Affinity_AbDarkKeeper Auto
Spell Property _00E_Affinity_AbFencer Auto
Spell Property _00E_Affinity_AbBladebreaker Auto
Spell Property _00E_Affinity_AbShadowdancer Auto
Spell Property _00E_Affinity_AbArcaneArcher Auto
Spell Property _00E_FS_Affinity_AbRitualist Auto
Spell Property _00E_FS_Affinity_AbGhostblade Auto
Spell Property _00E_FS_Affinity_AbSpectralWarrior Auto
Spell Property _00E_FS_Affinity_AbBrute Auto
Spell Property _00E_FS_Affinity_AbDrifter Auto
Spell Property _00E_FS_Affinity_AbDruid Auto
Spell Property _00E_FS_Affinity_AbNightwolf Auto
Spell Property _00E_FS_Affinity_AbRavager Auto
Spell Property _00E_FS_Affinity_AbScourge Auto
Spell Property _00E_FS_Affinity_AbSoulcaller Auto

Sound Property UIQuestCompleteM Auto

Quest Property NQ31 Auto

Formlist Property BastionPerks Auto
Formlist Property DerwishPerks Auto
Formlist Property ElementalismPerks Auto
Formlist Property EspionagePerks Auto
Formlist Property LifeAndDeathPerks Auto
Formlist Property ManipulationPerks Auto
Formlist Property RagePerks Auto
Formlist Property TrickeryPerks Auto
Formlist Property VagabondPerks Auto

; ADDED IN ENDERAL- FORGOTTEN STORIES
Formlist Property FS_PhasmalistPerks Auto
Formlist Property FS_TheriantrophistPerks Auto

Message Property _00E_FS_Game_PhasmalistName Auto
Message Property _00E_FS_Game_PhasmalistName_Female Auto
Message Property _00E_FS_Game_TheriantrophistName Auto
Message Property _00E_FS_Game_TheriantrophistName_Female Auto

Message Property _00E_FS_Game_Affinity_Spectralist Auto
Message Property _00E_FS_Game_Affinity_GhostBlade Auto
Message Property _00E_FS_Game_Affinity_SpectralWarrior Auto
Message Property _00E_FS_Game_Affinity_Spectralist_Female Auto
Message Property _00E_FS_Game_Affinity_GhostBlade_Female Auto
Message Property _00E_FS_Game_Affinity_SpectralWarrior_Female Auto
Message Property _00E_FS_Game_Affinity_Brute Auto
Message Property _00E_FS_Game_Affinity_Drifter Auto
Message Property _00E_FS_Game_Affinity_Druid Auto
Message Property _00E_FS_Game_Affinity_Nightwolf Auto
Message Property _00E_FS_Game_Affinity_Ravager Auto
Message Property _00E_FS_Game_Affinity_ScourgeOfTheWilds Auto
Message Property _00E_FS_Game_Affinity_Soulcaller Auto
Message Property _00E_FS_Game_Affinity_Brute_Female Auto
Message Property _00E_FS_Game_Affinity_Drifter_Female Auto
Message Property _00E_FS_Game_Affinity_Druid_Female Auto
Message Property _00E_FS_Game_Affinity_Nightwolf_Female Auto
Message Property _00E_FS_Game_Affinity_Ravager_Female Auto
Message Property _00E_FS_Game_Affinity_ScourgeOfTheWilds_Female Auto
Message Property _00E_FS_Game_Affinity_Soulcaller_Female Auto
;
FormList[] PerkTree_Trees
Message[] PerkTree_AffinityNames_Male
Message[] PerkTree_AffinityNames_Female

Int PerkTree_BastionIndex
Int PerkTree_DerwishIndex
Int PerkTree_ElementalismIndex
Int PerkTree_EspionageIndex
Int PerkTree_LifeAndDeathIndex
Int PerkTree_ManipulationIndex
Int PerkTree_RageIndex
Int PerkTree_TrickeryIndex
Int PerkTree_VagabondIndex
Int PerkTree_PhasmalistIndex
Int PerkTree_TheriantrophistIndex

Spell[] Affinity_Spells
Message[] Affinity_Names_Male
Message[] Affinity_Names_Female

Int Affinity_BattlemageIndex
Int Affinity_ClericIndex
Int Affinity_AssasinIndex
Int Affinity_WayfarerIndex
Int Affinity_BlackMageIndex
Int Affinity_DarkKeeperIndex
Int Affinity_FencerIndex
Int Affinity_BladebreakerIndex
Int Affinity_ShadowdancerIndex
Int Affinity_ArcaneArcherIndex
Int Affinity_WanderingMageIndex
Int Affinity_SpectralistIndex
Int Affinity_GhostBladeIndex
Int Affinity_SpectralWarriorIndex
Int Affinity_BruteIndex
Int Affinity_DrifterIndex
Int Affinity_DruidIndex
Int Affinity_NightwolfIndex
Int Affinity_RavagerIndex
Int Affinity_ScourgeOfTheWildsIndex
Int Affinity_SoulcallerIndex

Bool BlockClassUpdates

GlobalVariable Property _00E_MajorClassIndex  Auto  
GlobalVariable Property _00E_MinorClassIndex  Auto  

;KATAPUMB NEW AFFINITIES (ported to 2.1 by Zenderal)
Int Affinity_AcrobatIndex
Int Affinity_BerserkerIndex
Int Affinity_DragonHunterIndex
Int Affinity_DuelistIndex
Int Affinity_KnightIndex
Int Affinity_RiftMageIndex
Int Affinity_SlayerIndex
Int Affinity_SpellSwordIndex
Int Affinity_ThiefIndex
Int Affinity_WandererIndex
Int Affinity_WhiteMageIndex

Spell Property Kata_Affinity_AbAcrobat auto
Spell Property Kata_Affinity_AbBerserker auto
Spell Property Kata_Affinity_AbDragonHunter auto
Spell Property Kata_Affinity_AbDuelist auto
Spell Property Kata_Affinity_AbKnight auto
Spell Property Kata_Affinity_AbRiftMage auto
Spell Property Kata_Affinity_AbSlayer auto
Spell Property Kata_Affinity_AbSpellSword auto
Spell Property Kata_Affinity_AbThief auto
Spell Property Kata_Affinity_AbWanderer auto
Spell Property Kata_Affinity_AbWhiteMage auto

Message Property Kata_Game_Affinity_Acrobat auto
Message Property Kata_Game_Affinity_Acrobat_Female auto
Message Property Kata_Game_Affinity_Berserker auto
Message Property Kata_Game_Affinity_Berserker_Female auto
Message Property Kata_Game_Affinity_DragonHunter auto
Message Property Kata_Game_Affinity_DragonHunter_Female auto
Message Property Kata_Game_Affinity_Duelist auto
Message Property Kata_Game_Affinity_Duelist_Female auto
Message Property Kata_Game_Affinity_Knight auto
Message Property Kata_Game_Affinity_Knight_Female auto
Message Property Kata_Game_Affinity_RiftMage auto
Message Property Kata_Game_Affinity_RiftMage_Female auto
Message Property Kata_Game_Affinity_Slayer auto
Message Property Kata_Game_Affinity_Slayer_Female auto
Message Property Kata_Game_Affinity_SpellSword auto
Message Property Kata_Game_Affinity_SpellSword_Female auto
Message Property Kata_Game_Affinity_Thief auto
Message Property Kata_Game_Affinity_Thief_Female auto
Message Property Kata_Game_Affinity_Wanderer auto
Message Property Kata_Game_Affinity_Wanderer_Female auto
Message Property Kata_Game_Affinity_WhiteMage auto
Message Property Kata_Game_Affinity_WhiteMage_Female auto

;Version 1.3
Int Affinity_BardIndex
Int Affinity_EnchanterIndex
Int Affinity_ShadowCasterIndex

Spell Property Kata_Affinity_AbBard auto
Spell Property Kata_Affinity_AbEnchanter auto
Spell Property Kata_Affinity_AbShadowCaster auto

Message Property Kata_Game_Affinity_Bard auto
Message Property Kata_Game_Affinity_Bard_Female auto
Message Property Kata_Game_Affinity_Enchanter auto
Message Property Kata_Game_Affinity_Enchanter_Female auto
Message Property Kata_Game_Affinity_ShadowCaster auto
Message Property Kata_Game_Affinity_ShadowCaster_Female auto

;version 2.0
Int Affinity_IndexCustodio
Int Affinity_IndexHighlander
Int Affinity_IndexLunatic
Int Affinity_IndexMercenary
Int Affinity_IndexMonk
Int Affinity_IndexPackLeader
Int Affinity_IndexPoisoner
Int Affinity_IndexSoulReaper
Int Affinity_IndexWitcher
Int Affinity_IndexWolfHunter

Spell Property Kata_V2_Affinity_AbCustodio auto
Spell Property Kata_V2_Affinity_AbHighlander auto
Spell Property Kata_V2_Affinity_AbLunatic auto
Spell Property Kata_V2_Affinity_AbMercenary auto
Spell Property Kata_V2_Affinity_AbMonk auto
Spell Property Kata_V2_Affinity_AbPackLeader auto
Spell Property Kata_V2_Affinity_AbPoisoner auto
Spell Property Kata_V2_Affinity_AbSoulReaper auto
Spell Property Kata_V2_Affinity_AbWitcher auto
Spell Property Kata_V2_Affinity_AbWolfHunter auto

Message Property Kata_V2_Game_Affinity_Custodio auto
Message Property Kata_V2_Game_Affinity_Custodio_Female auto
Message Property Kata_V2_Game_Affinity_Highlander auto
Message Property Kata_V2_Game_Affinity_Highlander_Female auto
Message Property Kata_V2_Game_Affinity_Lunatic auto
Message Property Kata_V2_Game_Affinity_Lunatic_Female auto
Message Property Kata_V2_Game_Affinity_Mercenary auto
Message Property Kata_V2_Game_Affinity_Mercenary_Female auto
Message Property Kata_V2_Game_Affinity_Monk auto
Message Property Kata_V2_Game_Affinity_Monk_Female auto
Message Property Kata_V2_Game_Affinity_PackLeader auto
Message Property Kata_V2_Game_Affinity_PackLeader_Female auto
Message Property Kata_V2_Game_Affinity_Poisoner auto
Message Property Kata_V2_Game_Affinity_Poisoner_Female auto
Message Property Kata_V2_Game_Affinity_SoulReaper auto
Message Property Kata_V2_Game_Affinity_SoulReaper_Female auto
Message Property Kata_V2_Game_Affinity_Witcher auto
Message Property Kata_V2_Game_Affinity_Witcher_Female auto
Message Property Kata_V2_Game_Affinity_WolfHunter auto
Message Property Kata_V2_Game_Affinity_WolfHunter_Female auto

;END KATAPUMB
