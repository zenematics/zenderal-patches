Scriptname _00E_Game_SkillmenuSC extends ReferenceAlias
;
; ATTENTION
; this script contains a new affinity system that requires FS. Therefore, many elements in this script are redundant, as
; one version is required for the new system and one is required so that the old system can be used when FS is not
; available. If possible, the properties and functions are labeled with NEW or OLD in comments
;
;

Import Math
Import ActorValueInfo
Import _00E_QuestFunctions

; This script handles the custom character menu

;=====================================================================================
 ;                                      EVENTS                                   
;=====================================================================================

Event OnInit()

    FixedBugs1_2 = True
    iCurrentAffinityIndex = -1    
    InitAffinitySystem()

    InitializeActorValueInfos()
    UpdateKeyRegistration()
	RegisterForMenu("Journal Menu")
    
EndEvent

Event OnUpdate()

    UpdateKeyRegistration()
    
EndEvent

Event OnKeyDown(Int KeyCode)

    ; ZP: gamepad support. The modifier is tracked on its own so the open combo can be a chord,
    ; which SKSE's RegisterForKey cannot express by itself. Pressing it alone closes an open menu.
    If KeyCode == ZP_iGamepadModifier
        ZP_bGamepadModifierHeld = True
        If MenuOpen
            CloseSkillmenu()
        EndIf
        Return
    EndIf

    If KeyCode == iHeroMenuKeycode || (KeyCode == ZP_iGamepadOpenKey && ZP_bGamepadModifierHeld) || (MenuOpen && (KeyCode == iExitHeroMenuKeycode1 || KeyCode == iExitHeroMenuKeycode2))
        If !MenuOpen
            If Utility.IsInMenuMode() == False && UI.IsTextInputEnabled() == False && PlayerREF.GetCurrentLocation() != _00E_Dreamworld_Location && bReadyToOpen
                bReadyToOpen = False
                InitializeActorValueInfos()
                OpenSkillmenu()
                Utility.Wait(0.5)
                bReadyToOpen = True
            EndIf
        Else ; MenuOpen
            CloseSkillmenu()
        EndIf

    ElseIf KeyCode == iMeditateKeycode
        Spell meditateSpell = _00E_Class_Meditate.GetNthSpell(0)

        If PlayerREF.HasSpell(_00E_Class_Meditate) && Utility.IsInMenuMode() == False && UI.IsTextInputEnabled() == False && PlayerRef.IsOnMount() == False && Game.IsLookingControlsEnabled() == true && UI.IsMenuOpen("Dialogue Menu") == False && PlayerREF.GetCurrentLocation() != _00E_Dreamworld_Location
            meditateSpell.Cast(PlayerREF, PlayerREF)
        EndIf
	EndIf

EndEvent

; ZP: releases the gamepad chord modifier.
Event OnKeyUp(Int KeyCode, Float fHoldTime)

    If KeyCode == ZP_iGamepadModifier
        ZP_bGamepadModifierHeld = False
    EndIf

EndEvent

Event OnMenuClose(String MenuName)
    
	If MenuName == ("Journal Menu")
		UpdateKeyRegistration()
	EndIf

EndEvent

Event OnLocationChange(Location akOldLoc, Location akNewLoc)
    ; Gavrant:
    ; I don't know the purpose of re-registering keys on location change, but someone added this to _00E_Game_TalentControlSC in the first place.
    UpdateKeyRegistration()
EndEvent


;=====================================================================================
;                                       FUNCTIONS                                    
;=====================================================================================

Function _UpdateExitHeroMenuKeyRegistration(Int iExitKeycode)
    If iExitKeycode != iHeroMenuKeycode && iExitKeycode != iMeditateKeycode
        If MenuOpen
            RegisterForKey(iExitKeycode)
        Else
            UnregisterForKey(iExitKeycode)
        EndIf
    EndIf
EndFunction

Function UpdateKeyRegistration()
    RegisterForKey(iHeroMenuKeycode)

    RegisterForKey(iMeditateKeycode)
    bMeditateKeyRegistered = True

    ; ZP: gamepad chord, registered permanently - both halves are inert unless held together.
    RegisterForKey(ZP_iGamepadModifier)
    RegisterForKey(ZP_iGamepadOpenKey)

    _UpdateExitHeroMenuKeyRegistration(iExitHeroMenuKeycode1)
    _UpdateExitHeroMenuKeyRegistration(iExitHeroMenuKeycode2)
EndFunction

Function SetHeroMenuKey(int iNewKeyCode)
	UnregisterForKey(iHeroMenuKeycode)
	iHeroMenuKeycode = iNewKeyCode
    UpdateKeyRegistration()
EndFunction

Function SetMeditateKey(int iNewMeditateKeycode)
    UnregisterForKey(iMeditateKeycode)
    iMeditateKeycode = iNewMeditateKeycode
    UpdateKeyRegistration()
EndFunction

Function InitializeActorValueInfos()

    AiHealth = GetActorValueInfoByID(24)
    AiStamina = GetActorValueInfoByID(26)
    AiMagicka = GetActorValueInfoByID(25)

    AiRanged = GetActorValueInfoByID(8)            
    AiLightArmor = GetActorValueInfoByID(12)
    AiPsionics = GetActorValueInfoByID(21) ; Vanilla - Illusion
    AiElementarism = GetActorValueInfoByID(20); Vanilla - Destruction
    AiManipulation = GetActorValueInfoByID(18); Vanilla - Alteration
    AiOneHanded = GetActorValueInfoByID(6)     ; Vanilla - OneHanded
    AiTwoHanded = GetActorValueInfoByID(7)     ; Vanilla - TwoHanded
    AiParry = GetActorValueInfoByID(9)         ; Vanilla - Block
    AiLightMagic = GetActorValueInfoByID(22)   ; Vanilla - Restoration
    AiEntrophy = GetActorValueInfoByID(19) ; Vanilla - Conjuration
    AiHeavyArmor = GetActorValueInfoByID(11)       ; Vanilla - HeavyArmor
    AiSneak = GetActorValueInfoByID(15)            ; Vanilla - Sneak

    AiAlchemy = GetActorValueInfoByID(16)      ; Vanilla - Alchemy
    AiPickpocket = GetActorValueInfoByID(13)       ; Vanilla - Pickpocket
    AiEnchanting = GetActorValueInfoByID(23)       ; Vanilla - Enchanting
    AiLockpicking = GetActorValueInfoByID(14)  ; Vanilla - Lockpicking
    AiSmithing = GetActorValueInfoByID(10) ; Vanilla - Smithing
    AiSpeechcraft = GetActorValueInfoByID(17)  ; Vanilla - Speechcraft

EndFunction

Function OpenSkillmenu()
    
    If PlayerREF.GetCurrentLocation() != _00E_Dreamworld_Location
        MenuOpen = True

        UpdateKeyRegistration()
        
        ; if !Game.IsMovementControlsEnabled()
        ;    bControlsHaveBeenDisabled = True
        ; EndIf
        
        _00E_Game_MenuIMOD.Apply()
        UI.OpenCustomMenu("00E_heromenu")
        UI.InvokeStringA("CustomMenu", "_root.heromenu_mc.SetStringValues", GetStrings())
        UI.InvokeFloatA("CustomMenu", "_root.heromenu_mc.SetIntValues", GetFloats())
        UI.InvokeFloatA("CustomMenu", "_root.heromenu_mc.SetModifier", GetMods())
        
        RegisterForSingleUpdate(8)
        
    EndIf
    
EndFunction

Function CloseSkillmenu()

    UI.CloseCustomMenu()
    
    ; If !bControlsHaveBeenDisabled
        ; Game.EnablePlayerControls()
    ; EndIf
    
    ; bControlsHaveBeenDisabled = False
    
    _00E_Game_MenuIMOD.Remove()
    MenuOpen = False
    UpdateKeyRegistration()
    RegisterForSingleUpdate(15)
    
EndFunction

Float[] Function GetFloats()

    Float[] SkillmenuFloats = New Float[33]

    ; float fNeededEXP = ((pow((PlayerLevel.GetValueInt() + 1), EXPMultSlope.GetValue()) * EXPMult.GetValue()) - (pow(PlayerLevel.GetValueInt(), EXPMultSlope.GetValue()) * EXPMult.GetValue()))
    
    int iPlayerLevel = PlayerLevel.GetValueInt()
    float fEXPMultSlope = EXPMultSlope.GetValue()
    float fEXPMult = EXPMult.GetValue()
    float fEXPNeededForCurrentLevel = PlayerREF.ComputeNeededExp(iPlayerLevel - 1, fEXPMultSlope, fEXPMult)
    float fEXPNeededForNextLevel = PlayerREF.ComputeNeededExp(iPlayerLevel, fEXPMultSlope, fEXPMult)
    int iPlayerExp = PlayerExp.GetValueInt()
    
    SkillmenuFloats[0] =  (AiHealth.GetBaseValue(PlayerREF)) as Int
    SkillmenuFloats[1] =  AiHealth.GetCurrentValue(PlayerREF) as Int
    SkillmenuFloats[2] =  aiMagicka.GetBaseValue(PlayerREF) as Int
    SkillmenuFloats[3] =  aiMagicka.GetCurrentValue(PlayerREF) as Int
    SkillmenuFloats[4] =  aiStamina.GetBaseValue(PlayerREF) as Int
    SkillmenuFloats[5] =  aiStamina.GetCurrentValue(PlayerREF) as Int
    SkillmenuFloats[6] =  (-1*(PlayerREF.GetAV("LastFlattered"))) as Int
    SkillmenuFloats[7] =  fEXPNeededForNextLevel
    ;    (pow(PlayerLevel.GetValueInt(), EXPMultSlope.GetValue()) * (EXPMult.GetValue()*fEXPAcceleration))
    ;SkillmenuFloats[7] =  ((pow((PlayerLevel.GetValueInt()), EXPMultSlope.GetValue()) * EXPMult.GetValue()) - (pow(PlayerLevel.GetValueInt() - 1, EXPMultSlope.GetValue()) * EXPMult.GetValue())) as Float
    SkillmenuFloats[8] =  iPlayerExp
    SkillmenuFloats[9] =  iPlayerLevel
    SkillmenuFloats[10] = Lernpunkte.GetValueInt()
    SkillmenuFloats[11] = Handwerkspunkte.GetValueInt()
    SkillmenuFloats[12] = TalentPoints.GetValueInt()
    SkillmenuFloats[13] = aiPsionics.GetBaseValue(PlayerREF) as Int
    SkillmenuFloats[14] = aiElementarism.GetBaseValue(PlayerREF) as Int
    SkillmenuFloats[15] = aiManipulation.GetBaseValue(PlayerREF) as Int
    SkillmenuFloats[16] = aiOneHanded.GetBaseValue(PlayerREF) as Int
    SkillmenuFloats[17] = aiParry.GetBaseValue(PlayerREF) as Int
    SkillmenuFloats[18] = aiRanged.GetBaseValue(PlayerREF) as Int
    SkillmenuFloats[19] = aiEntrophy.GetBaseValue(PlayerREF) as Int
    SkillmenuFloats[20] = aiLightMagic.GetBaseValue(PlayerREF) as Int
    SkillmenuFloats[21] = aiTwoHanded.GetBaseValue(PlayerREF) as Int
    SkillmenuFloats[22] = aiLightArmor.GetBaseValue(PlayerREF) as Int
    SkillmenuFloats[23] = aiHeavyArmor.GetBaseValue(PlayerREF) as Int
    SkillmenuFloats[24] = aiSneak.GetBaseValue(PlayerREF) as Int
    SkillmenuFloats[25] = aiAlchemy.GetBaseValue(PlayerREF) as Int
    SkillmenuFloats[26] = aiPickpocket.GetBaseValue(PlayerREF) as Int
    SkillmenuFloats[27] = aiLockpicking.GetBaseValue(PlayerREF) as Int
    SkillmenuFloats[28] = aiEnchanting.GetBaseValue(PlayerREF) as Int
    SkillmenuFloats[29] = aiSmithing.GetBaseValue(PlayerREF) as Int
    SkillmenuFloats[30] = aiSpeechcraft.GetBaseValue(PlayerREF) as Int
    
    ; 31 Ist der F�llstand des Balkens (Beginnend bei 0)
    ; 32 ist der Maximalwert des Balkens (F�r gef�llten Balken)
    SkillmenuFloats[31] = iPlayerExp - fEXPNeededForCurrentLevel
    SkillmenuFloats[32] = fEXPNeededForNextLevel - fEXPNeededForCurrentLevel
    ; if PlayerExp.GetValueInt() == 1
        ; SkillmenuFloats[31] = PlayerExp.GetValueInt()
        ; SkillmenuFloats[32] = (pow(1, EXPMultSlope.GetValue()) * EXPMult.GetValue())
    ; Else
        ; SkillmenuFloats[31] = (PlayerExp.GetValueInt()-(pow((PlayerLevel.GetValueInt() - 1), EXPMultSlope.GetValue()) * EXPMult.GetValue()))
        ; SkillmenuFloats[32] = (pow(PlayerLevel.GetValueInt(), EXPMultSlope.GetValue()) * EXPMult.GetValue()) - (pow((PlayerLevel.GetValueInt() - 1), EXPMultSlope.GetValue()) * EXPMult.GetValue())
    ; EndIf
    
    Return SkillmenuFloats
    
EndFunction

Float[] Function GetMods()                      

;   Gets all modifiers applied to stats and skills

    Float[] SkillmenuMods = New Float[21]

    SkillmenuMods[0] =  ((aiHealth.GetMaximumValue(PlayerREF) as Int) - (aiHealth.GetBaseValue(PlayerREF) as Int))
    SkillmenuMods[1] =  ((aiMagicka.GetMaximumValue(PlayerREF) as Int) - aiMagicka.GetBaseValue(PlayerREF) as Int)
    SkillmenuMods[2] =  ((aiStamina.GetMaximumValue(PlayerREF) as Int) - aiStamina.GetBaseValue(PlayerREF) as Int)
    SkillmenuMods[3] =  ((aiPsionics.GetCurrentValue(PlayerREF) as Int) - aiPsionics.GetBaseValue(PlayerREF) as Int)
    SkillmenuMods[4] =  ((aiElementarism.GetCurrentValue(PlayerREF) as Int) - aiElementarism.GetBaseValue(PlayerREF) as Int)
    SkillmenuMods[5] =  ((aiManipulation.GetCurrentValue(PlayerREF) as Int) - aiManipulation.GetBaseValue(PlayerREF) as Int)
    SkillmenuMods[6] =  ((aiOneHanded.GetCurrentValue(PlayerREF) as Int) - aiOneHanded.GetBaseValue(PlayerREF) as Int)
    SkillmenuMods[7] =  ((aiParry.GetCurrentValue(PlayerREF) as Int) - aiParry.GetBaseValue(PlayerREF) as Int)
    SkillmenuMods[8] =  ((aiRanged.GetCurrentValue(PlayerREF) as Int) - aiRanged.GetBaseValue(PlayerREF) as Int)
    SkillmenuMods[9] =  ((aiEntrophy.GetCurrentValue(PlayerREF) as Int) - aiEntrophy.GetBaseValue(PlayerREF) as Int)
    SkillmenuMods[10] =  ((aiLightMagic.GetCurrentValue(PlayerREF) as Int) - aiLightMagic.GetBaseValue(PlayerREF) as Int)
    SkillmenuMods[11] =  ((aiTwoHanded.GetCurrentValue(PlayerREF) as Int) - aiTwoHanded.GetBaseValue(PlayerREF) as Int)
    SkillmenuMods[12] =  ((aiLightArmor.GetCurrentValue(PlayerREF) as Int) - aiLightArmor.GetBaseValue(PlayerREF) as Int) 
    SkillmenuMods[13] =  ((aiHeavyArmor.GetCurrentValue(PlayerREF) as Int) - aiHeavyArmor.GetBaseValue(PlayerREF) as Int)
    SkillmenuMods[14] =  ((aiSneak.GetCurrentValue(PlayerREF) as Int) - aiSneak.GetBaseValue(PlayerREF) as Int)
    SkillmenuMods[15] =  ((aiAlchemy.GetCurrentValue(PlayerREF) as Int) - aiAlchemy.GetBaseValue(PlayerREF) as Int)
    SkillmenuMods[16] =  ((aiPickpocket.GetCurrentValue(PlayerREF) as Int) - aiPickpocket.GetBaseValue(PlayerREF) as Int)
    SkillmenuMods[17] =  ((aiLockpicking.GetCurrentValue(PlayerREF) as Int) - aiLockpicking.GetBaseValue(PlayerREF) as Int)
    SkillmenuMods[18] =  ((aiEnchanting.GetCurrentValue(PlayerREF) as Int) - aiEnchanting.GetBaseValue(PlayerREF) as Int)
    SkillmenuMods[19] =  ((aiSmithing.GetCurrentValue(PlayerREF) as Int) - aiSmithing.GetBaseValue(PlayerREF) as Int)
    SkillmenuMods[20] =  ((aiSpeechcraft.GetCurrentValue(PlayerREF) as Int) - aiSpeechcraft.GetBaseValue(PlayerREF) as Int)
    
    Return SkillmenuMods
    
EndFunction

String[] Function GetStrings()

    String[] SkillmenuStrings = new string[2]
    
    SkillmenuStrings[0] = Player.GetName()
    SkillmenuStrings[1] = GetPlayerClassName()
  
    Return SkillmenuStrings
    
EndFunction

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

    Bool isFS = (_00E_FS_IsForgottenStoriesActivated.GetValueInt() == 1)

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

    If isFS
        PerkTree_PhasmalistIndex      = RegisterPerkTree(10, FS_PhasmalistPerks, _00E_FS_Game_PhasmalistName, _00E_FS_Game_PhasmalistName_Female)
		PerkTree_TheriantrophistIndex = RegisterPerkTree(11, FS_TheriantrophistPerks, _00E_FS_Game_TheriantrophistName, _00E_FS_Game_TheriantrophistName_Female)
    Else
        PerkTree_PhasmalistIndex 		= 10
		PerkTree_TheriantrophistIndex 	= 11
    EndIf

    ; Affinities
    Affinity_Spells       = New Spell[21]
    Affinity_Names_Male   = New Message[21]
    Affinity_Names_Female = New Message[21]

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

    If isFS
		Affinity_SpectralistIndex		= RegisterAffinity(11, _00E_FS_Affinity_AbRitualist, _00E_FS_Game_Affinity_Spectralist, _00E_FS_Game_Affinity_Spectralist_Female)
        Affinity_GhostBladeIndex		= RegisterAffinity(12, _00E_FS_Affinity_AbGhostblade, _00E_FS_Game_Affinity_GhostBlade, _00E_FS_Game_Affinity_GhostBlade_Female)
		Affinity_SpectralWarriorIndex	= RegisterAffinity(13, _00E_FS_Affinity_AbSpectralWarrior, _00E_FS_Game_Affinity_SpectralWarrior, _00E_FS_Game_Affinity_SpectralWarrior_Female)
		Affinity_BruteIndex				= RegisterAffinity(14, _00E_FS_Affinity_AbBrute, _00E_FS_Game_Affinity_Brute, _00E_FS_Game_Affinity_Brute_Female)
		Affinity_DrifterIndex			= RegisterAffinity(15, _00E_FS_Affinity_AbDrifter, _00E_FS_Game_Affinity_Drifter, _00E_FS_Game_Affinity_Drifter_Female)
		Affinity_DruidIndex				= RegisterAffinity(16, _00E_FS_Affinity_AbDruid, _00E_FS_Game_Affinity_Druid, _00E_FS_Game_Affinity_Druid_Female)
		Affinity_NightwolfIndex			= RegisterAffinity(17, _00E_FS_Affinity_AbNightwolf, _00E_FS_Game_Affinity_Nightwolf, _00E_FS_Game_Affinity_Nightwolf_Female)
		Affinity_RavagerIndex			= RegisterAffinity(18, _00E_FS_Affinity_AbRavager, _00E_FS_Game_Affinity_Ravager, _00E_FS_Game_Affinity_Ravager_Female)
		Affinity_ScourgeOfTheWildsIndex = RegisterAffinity(19, _00E_FS_Affinity_AbScourge, _00E_FS_Game_Affinity_ScourgeOfTheWilds, _00E_FS_Game_Affinity_ScourgeOfTheWilds_Female)
		Affinity_SoulcallerIndex		= RegisterAffinity(20, _00E_FS_Affinity_AbSoulcaller, _00E_FS_Game_Affinity_Soulcaller, _00E_FS_Game_Affinity_Soulcaller_Female)
    Else
        Affinity_SpectralistIndex 		= 11
        Affinity_GhostBladeIndex  		= 12
		Affinity_SpectralWarriorIndex 	= 13
		Affinity_BruteIndex 			= 14
		Affinity_DrifterIndex			= 15
		Affinity_DruidIndex				= 16
		Affinity_NightwolfIndex			= 17
		Affinity_RavagerIndex			= 18
		Affinity_ScourgeOfTheWildsIndex = 19
		Affinity_SoulcallerIndex		= 20
    EndIf


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

    ; Fix 1.2.x.x bugs if needed
    If FixedBugs1_2 == False
        If bHasAffinityBonus == False
            iCurrentAffinityIndex = -1
        EndIf

        If iCurrentAffinityIndex >= 0
            Spell affSpell = Affinity_Spells[iCurrentAffinityIndex]
            If PlayerREF.HasSpell(affSpell) == False
                PlayerREF.AddSpell(affSpell)
            EndIf
        EndIf

        Int[] PerkDistribution = GetPerkDistribution()
        UpdateClassIndices(PerkDistribution)

        FixedBugs1_2 = True

    Else

        ; Init MajorSchool
        If MajorSchool == 0
            UpdateMajorSchool()
        EndIf

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

int Function GetPointsInClass(Formlist akClassPerkformlist)

    Form[] perkForms = akClassPerkformlist.ToArray()
    int PointsSpentInClass

    int iClassIndex = 0
    While iClassIndex < perkForms.Length
        Perk iPerk = perkForms[iClassIndex] as Perk
        If iPerk && PlayerREF.HasPerk(iPerk)
            PointsSpentInClass += 1
        EndIf
        iClassIndex += 1
    EndWhile

    Return PointsSpentInClass
    
EndFunction

Int[] Function GetPerkDistribution()
    Int[] PerkDistribution = Utility.CreateIntArray(PerkTree_Trees.Length, 0)

    Int Index = 0
    While Index < PerkTree_Trees.Length
        If PerkTree_Trees[Index]
            PerkDistribution[Index] = GetPointsInClass(PerkTree_Trees[Index])
        EndIf
        Index += 1
    EndWhile

    Return PerkDistribution
EndFunction

Int[] Function GetMaxPerkDistribution()
    Int[] MaxPerkDistribution = Utility.CreateIntArray(PerkTree_Trees.Length, 0)

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
    Levelsystem.iMajorClassIndex = MajorClassIndex

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

    ; Levelsystem.iMinorClassIndex = MinorClassIndex

EndFunction

Function ResetUnlockedAffinities()
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

    ; Assassin/Assassine: Infiltraor und Klingent�nzer
    TryUnlockAffinity(PerkDistribution, Affinity_AssasinIndex, PerkTree_EspionageIndex, PerkTree_DerwishIndex)

    ; Wayfarer/Vielgereister: Vagabund und Gauner
    TryUnlockAffinity(PerkDistribution, Affinity_WayfarerIndex, PerkTree_VagabondIndex, PerkTree_TrickeryIndex)

    ; Black Mage/Schwarzmagier: Entropie und Elementarismus
    TryUnlockAffinity(PerkDistribution, Affinity_BlackMageIndex, PerkTree_LifeAndDeathIndex, PerkTree_ElementalismIndex)

    ; Black Keeper/Schwarzer H�ter: Sinistra und Bastion
    TryUnlockAffinity(PerkDistribution, Affinity_DarkKeeperIndex, PerkTree_LifeAndDeathIndex, PerkTree_BastionIndex)

    ; Fencer/Fechtmeister: Klingent�nzer und Vandale
    TryUnlockAffinity(PerkDistribution, Affinity_FencerIndex, PerkTree_DerwishIndex, PerkTree_RageIndex)

    ; Bladebreaker/Klingenbrecher:  Klingent�nzer/Bastion
    TryUnlockAffinity(PerkDistribution, Affinity_BladebreakerIndex, PerkTree_DerwishIndex, PerkTree_BastionIndex)

    ; Shadow Dancer/Schattent�nzer:  Infiltator und Sinistra/Thaumaturg
    TryUnlockAffinity(PerkDistribution, Affinity_ShadowdancerIndex, PerkTree_EspionageIndex, PerkTree_LifeAndDeathIndex)

    ; Wandering Mage/Wandermagier: Vagabund und Thaumaturg/Elementarist (currently not implemented)
    TryUnlockAffinity(PerkDistribution, Affinity_WanderingMageIndex, PerkTree_VagabondIndex, PerkTree_ElementalismIndex, PerkTree_ManipulationIndex)

    ; Arcane Archer/Arkaner Sch�tze: Gauner und Thaumaturg/Elementarist/Sinistra
    TryUnlockAffinity(PerkDistribution, Affinity_ArcaneArcherIndex, PerkTree_TrickeryIndex, PerkTree_ElementalismIndex, PerkTree_ManipulationIndex, PerkTree_LifeAndDeathIndex)

    ; Ritualist (Spectralist): Sinistrop und Phasmalist
    TryUnlockAffinity(PerkDistribution, Affinity_SpectralistIndex, PerkTree_PhasmalistIndex, PerkTree_LifeAndDeathIndex)

    ; Spectral Warrior: Phasmalist und Vandale/H�ter/Klingent�nzer
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

Endfunction

Function AddAchievementForAffinityUnlock(int nTotalUnlockedAffinityCount)

	If  _00E_AchievementsEnabled.GetValueInt() == 1
		If nTotalUnlockedAffinityCount >= 1
			Steam.UnlockAchievement("END_AFFINITY_01")
		EndIf
		If nTotalUnlockedAffinityCount >= 2
			Steam.UnlockAchievement("END_AFFINITY_02")
		EndIf
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
	
	If _00E_AchievementsEnabled.GetValueInt() == 1 && !bMemoryTreeAchievementUnlocked
		Int[] MaxPerkDistribution = GetMaxPerkDistribution()
		AddAchievementForFullMemoryTree(PerkDistribution, MaxPerkDistribution)
	EndIf

    ; What affinities are unlocked?
    Int iNewAffinityIndex = -1

    bool[] oldAffinities = affinitiesUnlocked as bool[] ; to really copy the array and not just copy the reference
    UpdateUnlockedAffinities(PerkDistribution)

    Int nTotalUnlockedAffinityCount = 0
	Int nSinceLastTimeUnlockedAffinityCount = 0
    Int[] unlockedAffinityIndices = Utility.CreateIntArray(affinitiesUnlocked.Length, 0)

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
        ElseIf _00E_FS_IsForgottenStoriesActivated.GetValueInt() == 1
            iNewAffinityIndex = AskForAffinityFS(unlockedAffinityIndices, nTotalUnlockedAffinityCount, iOldAffinity)

        ; Old ask
        Else 
            iNewAffinityIndex = AskForAffinityOld(unlockedAffinityIndices, nTotalUnlockedAffinityCount, iOldAffinity, oldAffinities)
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
            Levelsystem.GiveEP(450)
            NQ31.SetStage(10)
        EndIf
    EndIf

Endfunction

Int Function AskForAffinityOld(Int[] unlockedAffinityIndices, Int nUnlockedAffinities, Int iOldAffinity, Bool[] oldAffinities)

    ; Find first newly unlocked affinity, and fall back to first old unlocked affinity in case it fails
    Int iNewAffinity = -1
    Int iFallbackAffinity = -1

    Int Index = 0
    While Index < nUnlockedAffinities && iNewAffinity < 0
        Int iAffinity = unlockedAffinityIndices[Index]
        If iAffinity != iOldAffinity
            If oldAffinities[iAffinity] == False
                iNewAffinity = iAffinity
            EndIf
            If iFallbackAffinity < 0
                iFallbackAffinity = iAffinity
            EndIf
        EndIf
        Index += 1
    EndWhile

    If iNewAffinity < 0
        iNewAffinity = iFallbackAffinity
    EndIf

    If iNewAffinity >= 0 && iOldAffinity >= 0
        _00E_Affinity_Message_Actor_01.SetName(GetAffinityName(iOldAffinity))
        _00E_Affinity_Message_Actor_02.SetName(GetAffinityName(iNewAffinity))
        
        int iButton = _00E_Affinity_Messagebox.Show()

        if iButton == 0 ; Old
            Return iOldAffinity
        Elseif iButton == 2 ; Keep old and don't show again
            bDontShowAffinityMessageAgain = True
            Return iOldAffinity
        EndIf
    EndIf

    Return iNewAffinity

EndFunction

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

Event OnPlayerLoadGame()
    InitAffinitySystem()

    ; Post-1.2.5.0 update
    If bMeditateKeyRegistered == False
        UpdateKeyRegistration()
    EndIf

EndEvent


;=====================================================================================
;                                       PROPERTIES                                   
;=====================================================================================

_00E_QuestFunctions Property Levelsystem Auto

int iHeroMenuKeycode = 35

Int Property iExitHeroMenuKeycode1 = 15 AutoReadOnly ; 15 = TAB
Int Property iExitHeroMenuKeycode2 = 1 AutoReadOnly ; 1 = ESC

; ZP: SKSE gamepad keycodes. 277 = B, 266 = D-pad Up. Plain variables, not Properties, so the
; host plugin's VMAD property set is untouched.
int ZP_iGamepadModifier = 277
int ZP_iGamepadOpenKey = 266
bool ZP_bGamepadModifierHeld = False

int Property MajorClassIndex Auto Hidden
int Property MinorClassIndex Auto Hidden
int Property MajorSchool Auto
{ 1: Warrior; 2: Mage; 3: Thief }

int iCurrentAffinityIndex = -1
bool[] affinitiesUnlocked
bool bDontShowAffinityMessageAgain
bool bHasAffinityBonus = False  ; Left for backward compatibility with 1.2.x.x
bool bMemoryTreeAchievementUnlocked = False

bool bReadyToOpen = True
bool bStatsMenuOpen = False
; bool bControlsHaveBeenDisabled

ActorValueInfo AiHealth
ActorValueInfo AiStamina
ActorValueInfo AiMagicka

ActorValueInfo AiRanged         ; Vanilla - Marksman
ActorValueInfo AiLightArmor     ; Vanilla - Light Armor
ActorValueInfo AiPsionics       ; Vanilla - Illusion
ActorValueInfo AiElementarism   ; Vanilla - Destruction
ActorValueInfo AiManipulation   ; Vanilla - Alteration
ActorValueInfo AiOneHanded      ; Vanilla - OneHanded
ActorValueInfo AiTwoHanded      ; Vanilla - TwoHanded
ActorValueInfo AiParry          ; Vanilla - Block
ActorValueInfo AiLightMagic     ; Vanilla - Restoration
ActorValueInfo AiEntrophy       ; Vanilla - Conjuration
ActorValueInfo AiHeavyArmor     ; Vanilla - HeavyArmor
ActorValueInfo AiSneak          ; Vanilla - Sneak

ActorValueInfo AiAlchemy        ; Vanilla - Alchemy
ActorValueInfo AiPickpocket     ; Vanilla - Pickpocket
ActorValueInfo AiEnchanting     ; Vanilla - Enchanting
ActorValueInfo AiLockpicking    ; Vanilla - Lockpicking
ActorValueInfo AiSmithing       ; Vanilla - Smithing
ActorValueInfo AiSpeechcraft    ; Vanilla - Speechcraft

ActorBase Property Player Auto
_00E_EPUpdateFunctions Property PlayerREF Auto

ActorBase Property _00E_Affinity_Message_Actor_01 Auto
ActorBase Property _00E_Affinity_Message_Actor_02 Auto

bool MenuOpen = False

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

Message Property _00E_Affinity_Messagebox Auto
{Only necessary if FS is NOT used}
Message Property _00E_Affinity_MessageboxNew Auto
Message Property _00E_Affinity_MessageboxFirstAffinity Auto
Message Property _00E_Affinity_DoNotShowAgain Auto

Location Property _00E_Dreamworld_Location Auto

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

GlobalVariable Property PlayerExp Auto
GlobalVariable Property PlayerNeededExp Auto
GlobalVariable Property PlayerLevel Auto
GlobalVariable Property Lernpunkte Auto
GlobalVariable Property Handwerkspunkte Auto
GlobalVariable Property TalentPoints Auto
GlobalVariable Property EXPMultSlope Auto
GlobalVariable Property EXPMult Auto
GlobalVariable Property EXPAcceleration Auto
GlobalVariable Property _00E_FS_IsForgottenStoriesActivated Auto
GlobalVariable Property _00E_AchievementsEnabled Auto

ImageSpaceModifier Property _00E_Game_MenuIMOD Auto

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

Bool FixedBugs1_2
Bool BlockClassUpdates

Bool bMeditateKeyRegistered = False
Int Property iMeditateKeycode = 21 Auto Hidden ; 21 (Y on QWERTY, Z on QWERTZ)
Int Property iQuickStatsKeycode = 53 Auto Hidden ; 53 (/ on QWERTZ, - on QWERTY) 
Shout Property _00E_Class_Meditate Auto