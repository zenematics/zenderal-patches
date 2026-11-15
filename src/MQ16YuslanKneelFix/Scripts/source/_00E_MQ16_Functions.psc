Scriptname _00E_MQ16_Functions extends Quest Conditional

Import Utility

int function _GetScriptVersion() Global
    return 1
endFunction

;=====================================================================================
;                                        FUNCTIONS                                       
;=====================================================================================

Function SetUp()

    MQ15.ChooseCompanion()
    
    akCompanion = MQ15.akCompanion 
    akTealor = _00E_MC_TealorREF
    akYuslan = _00E_MC_YuslanREF
    
    Companion.ForceRefTo(akCompanion)
    
    if akYuslan.IsDisabled()
        akYuslan.Enable()
    EndIf
    
    If akCompanion.IsDisabled()
        akCompanion.Enable()
    EndIf
    
    akTealor.SetOutfit(MQ15._25E_HolyOrder_WardenOutfitNoHelmetNoCape)
    
    akYuslan.MoveTo(PlayerREF)
    
    akTealor.MoveTo(PlayerREF)
    akCompanion.MoveTo(PlayerREF)
    
    akYuslan.RemoveItem(Torch01)
    akYuslan.RemoveItem(Torch01RedDesat)
    
    akYuslan.EquipItem(akYuslan.GetEquippedWeapon(), True)
    akTealor.EquipItem(akTealor.GetEquippedWeapon(), True)
    akCompanion.EquipItem(akCompanion.GetEquippedWeapon(0), True)
    akCompanion.EquipItem(akCompanion.GetEquippedWeapon(1), True)
    
    MQ16_SC01_Journey_01.ForceStart()
    
    SetObjectiveDisplayed(5)
    
	_00E_Func_SetNPCAsCompanion.SetNPCAsCompanion(_00E_MC_TealorREF, True, 850, 550, 850)
	_00E_Func_SetNPCAsCompanion.SetNPCAsCompanion(_00E_MC_YuslanREF, True, 650, 550, 850)
	_00E_Func_SetNPCAsCompanion.SetNPCAsCompanion(akCompanion, True, 650, 700, 200)
	
EndFunction


Function PrepareVision_SC01()

    MQ16_SC01_MotherREF02.MoveTo(MQ16_SC01_MotherStartREF)
    MQ16_SC01_ChildREF02.MoveTo(MQ16_SC01_MotherREF02)
    MQ16_SC01_MotherREF02.SetAlpha(0.0)
    MQ16_SC01_ChildREF02.SetAlpha(0.0)
    MQ16_SC01_ChildREF02.GetActorBase().SetName("")
    MQ16_SC01_MotherREF02.GetActorBase().SetName("")

EndFunction


Function StartVision_SC01()

    MQ16_SC01_MotherREF02.EvaluatePackage()
    MQ16_SC01_ChildREF02.EvaluatePackage()
    MQ16_SC01_LinkMarker.Enable(False)
    MQ16_SC01_ChildREF02.SetAlpha(0.75)
    MQ16_SC01_MotherREF02.SetAlpha(0.75)
    MS04MemoryFXBody01VFX.Play(MQ16_SC01_MotherREF02)
    MS04MemoryFXBody01VFX.Play(MQ16_SC01_MotherREF02)
	
	if SKSE.GetVersion()
		MQ16_SC01_ChildREF02.GetActorBase().SetName(_00E_MQ16_sFleeingChild.GetName())
		MQ16_SC01_MotherREF02.GetActorBase().SetName(_00E_MQ16_sFleeingWoman.GetName())
	endif
	
    _00E_MQ16_SC01_ScreamM.Play(PlayerREF)
    _00E_MQ16_VisionIMOD.Apply()
    iVisionIntenseSound = _00E_AMB_Vision_SoundLPM.Play(PlayerREF)
    Wait(0.25)
    _00E_PlayerFunctions.GetVisionControl().VisionEffectTimestop(True, True)
    
EndFunction


Function StopVision_SC01()

    _00E_PlayerFunctions.GetVisionControl().VisionEffectTimestopStop()
    MQ16_SC01_LinkMarker.Disable()
    MQ16_SC01_ChildREF02.Disable()
    MQ16_SC01_MotherREF02.Disable()
    Sound.StopInstance(iVisionIntenseSound)
    ImageSpaceModifier.RemoveCrossFade()
    SetCurrentStageID(15)
    
EndFunction

Function StartSC02()

    MQ16_SC02_Journey_02.ForceStart()

EndFunction

Function DisableFollowerVision_SC03()

	_00E_Func_SetNPCAsCompanion.SetNPCAsCompanion(_00E_MC_TealorREF, False)
	_00E_Func_SetNPCAsCompanion.SetNPCAsCompanion(_00E_MC_YuslanREF, False)
	_00E_Func_SetNPCAsCompanion.SetNPCAsCompanion(akCompanion, False)

EndFunction

Function StartSC03()

    MQ16_SC03_Journey_03.ForceStart()

EndFunction

Function StartVision_SC03()

    MQ16_SC03_collisionREF.Enable()
    MQ16_SC03_VisionLinkerREF.Enable()
    iVisionIntenseSound = _00E_AMB_Vision_SoundLPM.Play(PlayerREF)
    _00E_PlayerFunctions.GetVisionControl().VisionEffectTimestop(True, True)
    _00E_MQ16_VisionIMOD.Apply()
    
EndFunction

Function StopVision_SC03()

    MQ16_SC03_KillBoxREF.Disable()
    akYuslan.UnequipItem(Torch01, True)
    akYuslan.UnequipItem(Torch01RedDesat, True)
    ;Debug.SendAnimationEvent(akYuslan, "IdleForceDefaultState")
    MQ16_SC03_collisionREF.Disable()
	MQ16_SC03_VisionVoice.Disable()
    MQ16_SC03_VisionLinkerREF.Disable()
    Sound.StopInstance(iVisionIntenseSound)
    _00E_PlayerFunctions.GetVisionControl().VisionEffectTimestopStop()
    ImageSpaceModifier.RemoveCrossFade()
    Wait(1)
    SetCurrentStageID(45)
    SetObjectiveDisplayed(12)
    
EndFunction

Function StartElevator()

    If MQ16_SC03_collisionREF.IsEnabled()
        MQ16_SC03_collisionREF.Disable()
    EndIf

    Wait(1)

EndFunction

Function StopElevatorSound()
    
    PlayerREF.SetGhost(False)
    SetCurrentStageID(45)
    
EndFunction

Function ReEnableCollision()

    Debug.ToggleCollisions()

EndFunction

Function StartSC04()

	_00E_Func_SetNPCAsCompanion.SetNPCAsCompanion(_00E_MC_TealorREF, True, 850, 550, 850)
	_00E_Func_SetNPCAsCompanion.SetNPCAsCompanion(_00E_MC_YuslanREF, True, 650, 550, 850)
	_00E_Func_SetNPCAsCompanion.SetNPCAsCompanion(akCompanion, True, 650, 700, 200)
	
    MQ16_SC04_Journey_04.ForceStart()

EndFunction

Function DisableFollower_SC04()

	_00E_Func_SetNPCAsCompanion.SetNPCAsCompanion(_00E_MC_TealorREF, False)
	_00E_Func_SetNPCAsCompanion.SetNPCAsCompanion(_00E_MC_YuslanREF, False)
	_00E_Func_SetNPCAsCompanion.SetNPCAsCompanion(akCompanion, False)
	; ZP: watch phase 3, where the scene waits for Yuslan to kneel (MQ16 Yuslan Kneel Fix)
	ZP_StartKneelWatch()

EndFunction

Function StartSC05()
	
    AudioCategoryMuteSubmerged.SetVolume(0.5)

    MQ16_SC05_HighOnes.ForceStart()
    
EndFunction

Function PosessCorpse01()

    MQ16_SC05_HighOnesEyes_03.EnableNoWait()
    _00E_VisionGlimpseWhisperM.Play(PlayerREF)
    _00E_StaggerSelf.Cast(akCompanion, akCompanion)
	
	if SKSE.GetVersion()
		MQ16_SC04_Corpse01REF.GetBaseObject().SetName(_00E_MQ16_sHighOnes.GetName())
		MQ16_SC04_Corpse02REF.GetBaseObject().SetName(_00E_MQ16_sHighOnes.GetName())
		MQ16_SC04_Corpse03REF.GetBaseObject().SetName(_00E_MQ16_sHighOnes.GetName())
		MQ16_SC04_Corpse04REF.GetBaseObject().SetName(_00E_MQ16_sHighOnes.GetName())
	endif
	
EndFunction

Function PosessCorpse02()

	if SKSE.GetVersion()
		MQ16_SC04_Corpse04REF.GetBaseObject().SetName(_00E_MQ16_sHighOnes.GetName())
	endif
	
    MQ16_SC05_HighOnesEyes_02.EnableNoWait()
    _00E_VisionGlimpseWhisperM.Play(PlayerREF)
    
EndFunction

Function PosessCorpse03()

    MQ16_SC05_HighOnesEyes_01.EnableNoWait(False)
    _00E_VisionGlimpseWhisperM.Play(PlayerREF)
	
	if SKSE.GetVersion()
		MQ16_SC04_Corpse03REF.GetBaseObject().SetName(_00E_MQ16_sHighOnes.GetName())    
    endif
	
EndFunction

Function PosessCorpse04()

    MQ16_SC05_HighOnesEyes_04.EnableNoWait()
    _00E_VisionGlimpseWhisperM.Play(PlayerREF)
	
	if SKSE.GetVersion()
		MQ16_SC04_Corpse02REF.GetBaseObject().SetName(_00E_MQ16_sHighOnes.GetName())
	endif
	
EndFunction

Function AddZyklusTheme()

    _00E_PlayerFunctions.GetSoundControl().RemoveSilence()
    _00E_Music_Special_Zyklus_OneSelection.Add()

EndFunction

Function AddZyklusLoop()

    _00E_PlayerFunctions.GetSoundControl().RemoveSilence()
    _00E_Music_Special_Zyklus_Loop.Add()

EndFunction

Function EnableMemory()
    
    MQ16_SC05_Irlanda.MoveTo(MQ16_SC05_IllusionIrlandaStartMarker)
    MQ16_SC05_Tealor.MoveTo(MQ16_SC05_IllusionTealorStartMarker)
    MQ16_SC05_Irlanda.Enable(True)
    MQ16_SC05_Tealor.Enable(True)
	_00E_Func_WaitForRef.WaitForReferenceToLoad(MQ16_SC05_Tealor)
    MQ16_SC05_Tealor.PlaceAtMe(ExplosionIllusionDark01, 1)
	_00E_Func_WaitForRef.WaitForReferenceToLoad(MQ16_SC05_Irlanda)
    MQ16_SC05_Irlanda.PlaceAtMe(ExplosionIllusionDark01, 1)
    _00E_HighOnesDisintegrate.Play(MQ16_SC05_Tealor)
    _00E_HighOnesDisintegrate.Play(MQ16_SC05_Irlanda)
    MQ16_SC05_Tealor.SetLookAt(MQ16_SC05_Irlanda)
    MQ16_SC05_Irlanda.SetLookAt(MQ16_SC05_Tealor)
    MQ16_SC05_Tealor.SetGhost(True)
    MQ16_SC05_Irlanda.SetGhost(True)
    MGTeleportInEffect.Play(MQ16_SC05_Irlanda)
    MGTeleportInEffect.Play(MQ16_SC05_Tealor)
    Wait(3)
    
EndFunction

Function TealorSheatheWeapon()

	_00E_EquipControl.SheatheWeapon(akTealor)

EndFunction

Function DisableMemory()

    MGTeleportOutEffect.Play(MQ16_SC05_Irlanda)
    MGTeleportOutEffect.Play(MQ16_SC05_Tealor)
    MQ16_SC05_Irlanda.DisableNoWait(True)
    MQ16_SC05_Tealor.DisableNoWait(True)
    
EndFunction

Function StartSC06()

    AudioCategoryMuteSubmerged.SetVolume(1.0)
    SetObjectiveDisplayed(10)
    FXFireOut.Play(akTealor)
    MQ16_SC05_HighOnesEyes_01.DisableNoWait()
    MQ16_SC05_HighOnesEyes_02.DisableNoWait()
    MQ16_SC05_HighOnesEyes_03.DisableNoWait()
    MQ16_SC05_HighOnesEyes_04.DisableNoWait()
	
	if SKSE.GetVersion()
		MQ16_SC04_Corpse04REF.GetBaseObject().SetName(_00E_MQ16_sCongealedCorpse.GetName())
		MQ16_SC04_Corpse03REF.GetBaseObject().SetName(_00E_MQ16_sCongealedCorpse.GetName())
		MQ16_SC04_Corpse02REF.GetBaseObject().SetName(_00E_MQ16_sCongealedCorpse.GetName())
		MQ16_SC04_Corpse01REF.GetBaseObject().SetName(_00E_MQ16_sCongealedCorpse.GetName())
	endif
	
    _00E_PlayerFunctions.GetSoundControl().RemoveSilence()
    _00E_Music_Combat_Epic.Add()
    
	_00E_Func_SetNPCAsCompanion.SetNPCAsCompanion(_00E_MC_TealorREF, True, 850, 550, 850)
	_00E_Func_SetNPCAsCompanion.SetNPCAsCompanion(_00E_MC_YuslanREF, True, 650, 550, 850)
	_00E_Func_SetNPCAsCompanion.SetNPCAsCompanion(akCompanion, True, 650, 700, 200)
    
    MQ16_SC06_Assault.ForceStart()

    ReanimateCorpses(1)
    
EndFunction

Function ReanimateCorpses(int iStage)

    Game.RequestAutoSave()
    
    int iReanimateIndex 
    
    if iStage == 1
        MQ16_SC06_BossREF.Enable()
        MQ16_SC06_BossREF.Activate(MQ16_SC06_BossREF)
        MQ16_SC06_BossREF.PlaceAtMe(ExplosionIllusionMassiveDark01)
        Wait(1)
        iReanimateIndex = _00E_MQ16_SC06_Stage01_Enemies.GetSize()

        while iReanimateIndex > 0
            iReanimateIndex -= 1
            _00E_MQ16_HighOnes_Echo_DeadSC CorpseREF = _00E_MQ16_SC06_Stage01_Enemies.GetAt(iReanimateIndex) as _00E_MQ16_HighOnes_Echo_DeadSC
            CorpseREF.Enable()
            ; CorpseREF.Resurrect()
            _00E_MQ16_RessurectSP.Cast(MQ16_SC06_ProjectileSpawn, CorpseREF)
            CorpseREF.Reanimate()
            CorpseREF.StartCombat(PlayerREF)
        EndWhile
        
    Elseif iStage == 2
    
        iReanimateIndex = _00E_MQ16_SC06_Stage02_Enemies.GetSize()

        while iReanimateIndex > 0
            iReanimateIndex -= 1
            _00E_MQ16_HighOnes_Echo_DeadSC CorpseREF = _00E_MQ16_SC06_Stage02_Enemies.GetAt(iReanimateIndex) as _00E_MQ16_HighOnes_Echo_DeadSC
            CorpseREF.Enable()
            CorpseREF.Reanimate()
            CorpseREF.StartCombat(PlayerREF)
        EndWhile
    
    Else
        MQ16_SC06_Stage03_Mage_01REF.Enable()
        MQ16_SC06_Stage03_Mage_01REF.Activate(MQ16_SC06_Stage03_Mage_01REF)
        MQ16_SC06_Stage03_ZombieGiantREF.Enable()
        MQ16_SC06_Stage03_ZombieGiantREF.PlaceAtMe(ExplosionIllusionMassiveDark01)
        GhostRedFXShader.Play(MQ16_SC06_Stage03_ZombieGiantREF)
        MQ16_SC06_Stage03_ZombieGiantREF.AddSpell(GhostAbilityRed)
        MQ16_SC06_Stage03_ZombieGiantREF.StartCombat(PlayerREF)
        
        iReanimateIndex = _00E_MQ16_SC06_Stage03_Enemies.GetSize()

        while iReanimateIndex > 0
            iReanimateIndex -= 1
            _00E_MQ16_HighOnes_Echo_DeadSC CorpseREF = _00E_MQ16_SC06_Stage03_Enemies.GetAt(iReanimateIndex) as _00E_MQ16_HighOnes_Echo_DeadSC
            CorpseREF.Enable()
            CorpseREF.Reanimate()
        EndWhile
    
    EndIf

EndFunction

Function Stage01_PickTargets()

    akYuslan.StartCombat(MQ16_SC06_Stage01_YuslanJesparTarget)
    akCompanion.StartCombat(MQ16_SC06_Stage01_YuslanJesparTarget)
    akTealor.StartCombat(MQ16_SC06_BossREF)
    MQ16_SC06_BossREF.StartCombat(PlayerREF)
    
EndFunction

Function RemoveCombatMusic()
	
	_00E_Func_SetNPCAsCompanion.SetNPCAsCompanion(_00E_MC_TealorREF, False)
	_00E_Func_SetNPCAsCompanion.SetNPCAsCompanion(_00E_MC_YuslanREF, False)
	_00E_Func_SetNPCAsCompanion.SetNPCAsCompanion(akCompanion, False)
    SetObjectiveCompleted(10)
    _00E_Music_Combat_Epic.Remove()
    
EndFunction

Function StartSC07()
    
    Game.DisablePlayerControls()
    MQ16_SC07_DragonAttack.ForceStart()

EndFunction

Function DragonRise_Stage01()

    MQ16_SC07_HighOnesOrb01.Enable()
    MQ16_SC07_HighOnesOrb02.Enable()
    MQ16_SC07_UndeadDragonREF.Enable()
    MQ16_SC07_UndeadDragonREF.SetAlpha(0)
    NPCDragonSkeletalResurrectionRumble01.Play(PlayerREF)
    Wait(1)
    NPCDragonSkeletalResurrectionRoarAM.Play(PlayerREF)

EndFunction

Function DragonRise_Stage02()
            
    Game.ShakeCamera()
    PlayerREF.KnockAreaEffect(0.5, 1024)
    MQ16_SC07_UndeadDragonREF.AddSpell(GhostAbilityRed)
    MQ16_SC07_UndeadDragonREF.SetLookAt(PlayerREF)
    MQ16_SC07_WallPlane004.Enable()
    MQ16_SC07_WallPlane002.Enable()
    MQ16_SC07_WallPlane003.Enable()
    MAGConjureBoundWeaponAppearM.Play(PlayerREF)
    MQ16_SC07_HighOnesOrb01.PlayAnimation("PlayAnim02")
    MQ16_SC07_HighOnesOrb02.PlayAnimation("PlayAnim02")
    MQ16_SC07_UndeadDragonREF.SetAllowFlying(True)
    MQ16_SC07_UndeadDragonREF.SetAnimationVariableBool("bAnimationDriven", false)
    MQ16_SC07_UndeadDragonREF.SetAnimationVariableBool("bMotionDriven", true)
    NPCDragonTakeoffFX.Play(MQ16_SC07_UndeadDragonREF)
    Debug.SendAnimationEvent(MQ16_SC07_UndeadDragonREF, "TakeOff_Vertical")
    NPCDragonWingFlapTakeoff.Play(PlayerREF)
    Wait(3)
    Debug.SendAnimationEvent(MQ16_SC07_UndeadDragonREF, "FlyStartHover")
    NPCDragonWingFlapTakeoff.Play(PlayerREF)
    bDragonFire = True
    MQ16_SC07_UndeadDragonREF.EvaluatePackage()
    NPCDragonSkeletalResurrectionRoarBM.Play(PlayerREF)
    
EndFunction

Function Impact()

	FXExplosionCatapultNearM.Play(PlayerREF)
	Game.ForceFirstPerson()
	MAGFireBallExpDragonImod.Apply()
	MQ16_SC07_DragonStrikeImpactStonesREF.Enable(False)
	MQ16_SC07_DragonStrikeImpactMarkerREF.PlaceAtMe(FireBallExp01Big)
	MQ16_SC07_CollapseCloudFXREF.Enable()
	Wait(1)
	MQ16_SC07_DragonStrikeImpactMarkerREF.Enable()
	MQ16_SC07_CollapseCloudFXREF.PlayAnimation("PlayAnim02")
	MQ16_SC07_DragonStrikeImpactMarkerREF.PlaceAtMe(FireStormExplosion)
	MQ16_SC07_DragonStrikeImpactStonesREF.PlayAnimation("PlayAnim02")
	MQ16_SC07_DragonStrikeImpactMarkerREF.KnockAreaEffect(1,2048)
	game.shakeCamera(afStrength = 0.5)
	_00E_A1_RocksolidOutM.Play(PlayerREF)
	Wait(1)
	PlayerREF.TranslateTo(PlayerREF.GetPositionX(), PlayerREF.GetPositionY(), (PlayerREF.GetPositionZ() - 50), PlayerREF.GetAngleX(), PlayerREF.GetAngleY(), PlayerREF.GetAngleZ(), 75)
	game.shakeCamera(afStrength = 1)
	Wait(0.35)
	QSTTG05ArrowKnockOut2D.Play(PlayerREF)
	FadeToBlackHoldImod.Apply()
	Wait(4)
	SetCurrentStageID(80)

EndFunction

Function StartSC08()

    FadeToBlackHoldImod.Apply()
    akYuslan.MoveTo(MQ16_SC08_YuslanStart)
    akTealor.MoveTo(MQ16_SC08_TealorStart)
    PlayerREF.MoveTo(MQ16_SC08_PlayerStart)
    _00E_BloodyFXShader.Play(akTealor)
    _00E_BloodyFXShader.Play(akYuslan)
    _00E_BloodyFXShader.Play(PlayerREF)
    Game.TriggerScreenBlood(1)
    PlayerREF.PlayIdle(TG05_Knockout)
    
    MQ16_SC08_Temple_01.ForceStart()
    
EndFunction

Function WakeUp()

    _00E_Func_AIWalk.PlayerAIWalkStop()
    GetUp()
    FadeToBlackHoldImod.Remove()
    _00E_MQ02_WakeUp.ApplyCrossFade()
    MAGVampireSunlight.Play(PlayerREF)
    
EndFunction

Function GetUp()

    PlayerREF.PlayIdle(TG05_GetUp)

EndFunction

Function StartSC09()
    
	_00E_Func_SetNPCAsCompanion.SetNPCAsCompanion(_00E_MC_TealorREF, True, 850, 550, 850)
	_00E_Func_SetNPCAsCompanion.SetNPCAsCompanion(_00E_MC_YuslanREF, True, 650, 550, 850)
	
    MQ16_SC09_Temple_02.ForceStart()
	
EndFunction

Function StartVision_SC09()
	
    _00E_MQ16_VisionIMOD.Apply()
	
    iVisionIntenseSound = _00E_MQ16_BattlefieldVisionM.Play(PlayerREF)
    MQ16_SC09_VisionLinkREF.Enable()
    _00E_PlayerFunctions.GetVisionControl().VisionEffectNoTimestop(MQ16_SC09_VisionNPCs)
	
    MQ16_SC09_Vision_EnemyREF.PlayIdleWithTarget(pa_2HMKillMoveDecapSlash, MQ16_SC09_Vision_SoldierREF)
		
    Wait(5.5)
    StopVision_SC09()
    
EndFunction

Function StopVision_SC09()

    _00E_PlayerFunctions.GetVisionControl().VisionEffectNoTimestopStop(MQ16_SC09_VisionNPCs)
    MQ16_SC09_VisionLinkREF.Disable()
    Sound.StopInstance(iVisionIntenseSound)
    ImageSpaceModifier.RemoveCrossFade()
    SetCurrentStageID(100)
    _00E_MQ16_Temple_Thoughts_01.ShowAsHelpMessage("_00E_MQ16_Temple_Thoughts_01", 5, 1, 1)
    
EndFunction

Function StartSC10()

    EnableNPCsInFormlist(MQ16_SC10_VisioNPCs)
    MQ16_SC10_Temple_03.ForceStart()

EndFunction

Function PrepareVision_SC10()

    MQ16_SC10_VisionPriestess.Kill(MQ16_SC10_VisionPriestess)
    MQ16_SC10_VisionLinker.Enable()
    MQ16_SC10_VisionPriestess.MoveToMyEditorLocation() ; otherwise snaps to navmesh
    
EndFunction

Function EnableNPCsInFormlist(Formlist formlistNPCs)

    int iIndex = formlistNPCs.GetSize()
    
    while iIndex > 0
        iIndex -= 1
        _00E_VisionFX_NPC_SC npcToEnable = formlistNPCs.GetAt(iIndex) as _00E_VisionFX_NPC_SC
        npcToEnable.SetAlphaAndFX()
    endwhile
    
EndFunction

Function StartVision_SC10()

    MQ16_SC10_SmokeREF.EnableNoWait(False)
    MQ16_SC10_VisionKidREF.SetAlphaAndFX()
    MQ16_SC10_VisionPriestess.SetAlphaAndFX()
    iVisionIntenseSound = _00E_AMB_Vision_SoundLPM.Play(PlayerREF)
    _00E_MQ16_VisionIMOD.Apply()
    _00E_PlayerFunctions.GetVisionControl().VisionEffectTimestop(True, True)
    
EndFunction

Function StopVision_SC10()

    _00E_PlayerFunctions.GetVisionControl().VisionEffectTimestopStop(False)
    MQ16_SC10_SmokeREF.Disable()
    MQ16_SC10_VisionLinker.Disable()
    Sound.StopInstance(iVisionIntenseSound)
    ImageSpaceModifier.RemoveCrossFade()
    SetCurrentStageID(110)
    
EndFunction

Function PrepareVision_02_SC10()

    MQ16_SC10_Vision_02_Linker.Enable()

EndFunction

Function StartVision_02_SC010()

    _00E_MQ16_VisionIMOD.Apply()
    iVisionIntenseSound = _00E_AMB_Vision_SoundLPM.Play(PlayerREF)
    EnableNPCsInFormlist(MQ16_SC10_Vision_02_NPCs)
    _00E_PlayerFunctions.GetVisionControl().VisionEffectTimestop(True, True)
    
EndFunction

Function StopVision_02_SC010()

    MQ16_SC10_Vision_02_Linker.Disable()
    _00E_PlayerFunctions.GetVisionControl().VisionEffectTimestopStop(False)
    Sound.StopInstance(iVisionIntenseSound)
    ImageSpaceModifier.RemoveCrossFade()
    
EndFunction

Function EnableWordOfTheDead()

    MAGIllusionCharm.Play(MQ16_SC10_WordOfTheDeadREF)
    MQ16_SC10_WordOfTheDeadREF.Enable()
    MQ16_SC10_WordOfTheDeadREF.SetPosition(-5939.0, -2420.0, 1453.0)
    MQ16_SC10_WordOfTheDeadREF.SetAngle(0.0, 0.0, 90)

EndFunction

Function UpdateEchoCount()

    MQ16_EchoCluesFound.SetValue(MQ16_EchoCluesFound.GetValueInt() + 1)
    Self.UpdateCurrentInstanceGlobal(MQ16_EchoCluesFound)
    
    int CurrentCount = MQ16_EchoCluesFound.GetValueInt()

    if CurrentCount >= 5
        Self.SetObjectiveCompleted(25, 1)
        Self.SetCurrentStageID(135)
    ElseIf CurrentCount < 5
        Self.SetObjectiveCompleted(25,0)
        Self.SetObjectiveDisplayed(25, True, True)
    EndIf

EndFunction

Function PlayVisionFragment(int iVisionFragmentIndex, ObjectReference objSelfRef, float iDuration)

    formlistVisionShader 
    formlistVisionShader.AddForm(objSelfRef)
    _00E_PlayerFunctions.GetVisionControl().VisionEffectNoTimestop(formlistVisionShader, MQ16_SC11_VisionFormlist)
    iVisionIndexFragment = iVisionFragmentIndex
    MQ16_SC10_VisionActorREF.Say(MQ16_D03_VisionFragmentTopic, None, True)
    Wait(8.0)
    MQ16_SC10_VisionActorREF.Disable()
    StopVisionFragment()
    UpdateEchoCount()
    
EndFunction

Function StopVisionFragment()

    _00E_PlayerFunctions.GetVisionControl().VisionEffectNoTimestopStop(formlistVisionShader, MQ16_SC11_VisionFormlist, false)
    MQ16_SC10_VisionActorREF.Enable()
    
EndFunction

Function StartSC11()

    Game.RequestAutoSave()
    EnableWordOfTheDead()
    MQ16_SC11_Temple_04.ForceStart()

EndFunction

Function StartCleansingMemory()
    
    _00E_Music_Special_Zyklus_Loop.Remove()
    _00E_SilenceTransitionHighPriority.Add()
    _00E_VisionShaderParticles.Apply(1)
    _00E_MQ16_SC11_VisionCleansingBuildUpIMOD.Apply()
    _00E_MQ16_EchoCleansingM.Play(PlayerREF)
    Wait(1)
    _00E_VisionShaderParticles.Apply(1)
    Game.ShakeCamera(afStrength = 0.25, afDuration = 12)
    Wait(9)
    _00E_MQ16_EchoCleansingIMOD.ApplyCrossFade(afFadeDuration = 0.1)

    Wait(7)
    MQ16_SC11_WordOfTheDeadMagic.SetPosition(5942, 2422, 1456)
    akTealor.Say(MQ16_D03_VisionFragmentTopic)
    bYuslanRunToWordOfTheDead = True
    akYuslan.PlayIdle(_00E_IdleCastMagicTwoHanded)
    MQ16_SC10_WordOfTheDeadREF.SetOpen(True)
    MQ16_SC11_WordOfTheDeadMagic.Enable()
    Game.ShakeCamera(afStrength = 1, afDuration = 26)
    Wait(25.5)
    FadeToWhiteHoldImod.ApplyCrossFade(afFadeDuration = 0.25)
    SetCurrentStageID(140)

EndFunction

Function StartSC12()

    _00E_VisionShaderParticles.Remove(1)
    PlayerREF.MoveTo(MQ16_SC12_PlayerStartREF)
    akTealor.MoveTo(MQ16_SC12_TealorStartREF)
    akYuslan.MoveTo(MQ16_SC12_YuslanStartREF)
    MS04MemoryFXBody01VFX.Play(akTealor)
    MS04MemoryFXBody01VFX.Play(akYuslan)
    MS04MemoryFXBody01VFX.Play(PlayerREF)
    Debug.SendAnimationEvent(akTealor, "IdleBedRollFrontEnterInstant")
    Debug.SendAnimationEvent(akYuslan, "IdleBedRollFrontEnterInstant")
    PlayerREF.PlayIdle(TG05_Knockout)
    Game.ShakeCamera(afStrength = 0.0)
    Game.RequestAutoSave()
    
    MQ16_SC12_Numinos.ForceStart()


EndFunction

Function GetUpEveryone()
    
    _00E_WakeUp.ApplyCrossFade(afFadeDuration = 1.0)
    PlayerREF.PlayIdle(TG05_GetUp)
    Wait(2)
    Debug.SendAnimationEvent(akTealor, "_00E_BedrollFrontExit")
    Wait(0.8)
    Debug.SendAnimationEvent(akYuslan, "_00E_BedrollFrontExit")
    PlayerREF.AddSpell(_00E_MQ16_WeakenedAbSP)
    
    ; And now for something completely different: Remove
    ; akCompanion's torch so they have their hands free for the MQ17
    ; fight against the Black Guardian.
    akCompanion.UnequipItem(Torch01)
    akCompanion.RemoveItem(Torch01)
    
EndFunction


Function AddNuminosMusic()

    _00E_Music_Special_MQ16_Numinos.Add()

EndFunction

Function YuslanTeleport()

    _00E_MQ15_EldricthDissolveFXS.Play(akYuslan)
    Wait(1)
    akYuslan.PlaceAtMe(_00E_MAGEldritchShockExplosionTeleport)
    Wait(0.5)
    akYuslan.MoveTo(MQ16_SC12_YuslanTeleportMarkerREF)
    akYuslan.PlaceAtMe(_00E_MAGEldritchShockExplosionTeleport)
    _00E_Ability_ShadowrunTeleportSoundM.Play(akYuslan)
    _00E_MQ15_EldricthDissolveFXS.Stop(akYuslan)
    _00E_EldritchTeleportReappear.Play(akYuslan)
    Wait(2.5)
    _00E_EldritchTeleportReappear.Stop(akYuslan)

    
EndFunction

Function StartSC13()

    MQ16_SC13_Numinos_02.ForceStart()

    akYuslan.AddSpell(_00E_AbPosessed)
    MQ16_SC13_BarrierREF.Enable(False)
    MQ16_SC13_CollisionREF.Enable()
    akYuslan.PlayIdle(IdleMagic_01)
    _00E_MAGEldritchFireSS1M.Play(akYuslan)

EndFunction

Function YuslanSuicide()

    _00E_MQ15_EldricthDissolveFXS.Play(akYuslan)
    Wait(1)
    akYuslan.PlaceAtMe(_00E_MAGEldritchShockExplosionTeleport)
    Wait(0.25)
    
    akYuslan.PlaceAtMe(_00E_MQ16_YuslanSuicideExplosion)
    akYuslan.PlaceAtMe(_00E_FS_MAGGoreExplosion)
	Game.TriggerScreenBlood(10)
    PlayerREF.KnockAreaEffect(1, 1024)
    Game.ShakeCamera(afStrength = 1)
    _00E_MQ16_SC13_YuslanSuicideIMOD.Apply()
    MQ16_SC13_BarrierREF.PlayAnimation("playAnim01")
    MQ16_SC13_BarrierREF.Disable()
    akYuslan.SetAlpha(0.0)
    akYuslan.Disable()
    
    int iShrinkTimer = 90
    
    if MQ16_SC13_NuminosREF != None
    
        while iShrinkTimer > 0
            MQ16_SC13_NuminosREF.SetScale(MQ16_SC13_NuminosREF.GetScale() - 0.1)
            iShrinkTimer -= 1
        endwhile
        
    EndIf
    
    MQ16_SC13_NuminosREF.PlaceAtMe(ExplosionIllusionDark01)
    MQ16_SC13_NuminosREF.Disable()
    
EndFunction

Function StartEarthquake()

    SetObjectiveFailed(30)
    Game.ShakeCamera(afStrength = 0.5, afDuration = 10)
    QSTDA10Rumble.Play(PlayerREF)
    Wait(1.5)
    _00E_MQ11c_DreamCollapseIMOD.Apply()
    AMBRumbleShake.Play(PlayerREF)
    _00E_MQ11c_RyneusTransformSoundM.Play(PlayerREF)
    akTealor.Say(MQ16_D03_VisionFragmentTopic)
    Debug.SendAnimationEvent(akTealor, "IdleBoundKneesStart")
    Wait(11)
    FadeToBlackHoldImod.ApplyCrossFade(afFadeDuration = 0.25)
    Wait(2)
    SetCurrentStageID(165)
    
EndFunction

Function StartSC14()

    ; FAILSAVE: This should be harmless, but can be deleted after beta.
    
    MQ16S_SC14_YuslanStartMarker.SetPosition(-5730.1968, -2338.8777, 1385.7076)
    MQ16_SC14_PlayerWoundedMarker.SetPosition(-5416.3809, -2445.6357, 1324.7621)
    MQ16_SC14_TealorStart.SetPosition(-5906.2764, -2424.5933, 1446.6113)
    
    ; FAILSAVE: This should be harmless, but can be deleted after beta.

    Game.TriggerScreenBlood(1)
    Game.DisablePlayerControls(true, true, true, false, true, true, true)
    Game.ForceFirstPerson()
    MS04MemoryFXBody01VFX.Stop(akTealor)
    MS04MemoryFXBody01VFX.Stop(PlayerREF)
    MQ16_SC14_YuslanDeadREF.GetActorBase().SetEssential(False)
    MQ16_SC14_YuslanDeadREF.SetGhost(False)
	
	if SKSE.GetVersion()
		MQ16_SC14_YuslanDeadREF.GetActorBase().SetName(_00E_MQ16_sHighOnes.GetName())
	endif
	
    akTealor.MoveTo(MQ16_SC14_TealorStart)
    PlayerREF.MoveTo(MQ16_SC14_PlayerWoundedMarkerFailsave)
    _00E_ShatterSoulDarkFlamesShader.Play(MQ16_SC14_YuslanDeadREF)
    _00E_BloodyFXShader.Play(MQ16_SC14_YuslanDeadREF)
    _00E_BloodyFXShader.Play(PlayerREF)
    _00E_BloodyFXShader.Play(akTealor)
    MQ16_SC14_YuslanDeadREF.Enable()
    MQ16_SC14_YuslanDeadREF.MoveTo(MQ16_SC14_YuslanBedRoll)
    MQ16_SC11_WordOfTheDeadMagic.Disable()
    MQ16_SC10_WordOfTheDeadREF.Enable()
    MQ16_SC10_WordOfTheDeadREF.SetOpen(True)
    MQ16_SC14_YuslanDeadREF.SetOutfit(_00E_MC_Yarim_Outfit)

    Game.RequestAutoSave()
    MQ16_SC14_Temple.ForceStart()

EndFunction

Function PlayerWakeUp()

    Wait(1)
    _00E_MQ02_WakeUp.Apply()
    Wait(4)
    _00E_MQ16_HeadacheLoopImod.ApplyCrossFade(afFadeDuration = 2.0)
    
EndFunction

Function TealorGetUp()

    akTealor.SetLookAt(MQ16_SC14_YuslanDeadREF)
    akTealor.PlayIdle(IdleExhaustedExit)
    _00E_ShatterSoulDarkFlamesShader.Stop(MQ16_SC14_YuslanDeadREF)
    
EndFunction

Function TealorHitYuslan()

    Debug.SendAnimationEvent(akTealor, "attackPowerStartInPlace")
    Wait(0.25)
    _00E_BloodyFXShader.Play(MQ16_SC14_YuslanDeadREF)
    MQ16_SC14_YuslanDeadREF.PlayImpactEffect(BloodSprayImpactSetRed)
    WPNImpactBlade2HandVsFlesh.Play(MQ16_SC14_YuslanDeadREF)
    Game.ShakeCamera(afStrength = 0.25)
    akTealor.SetActorValue("SpeedMult", 65)
    
EndFunction

Function PosessYuslan()
    
    MQ16_SC14_YuslanDeadREF.RegenerateHead()
    MQ16_SC14_YuslanDeadREF.PlaceAtMe(_00E_MQ16_HighOnesRedLight)
	
	if SKSE.GetVersion()
		MQ16_SC14_YuslanDeadREF.GetActorBase().SetName(_00E_MQ16_sHighOnesThroughYuslan.GetName())
	endif
	
    GhostRedFXShader.Play(MQ16_SC14_YuslanDeadREF)
    MQ16_SC14_YuslanDeadREF.AddSpell(_00E_AbPosessed)
    _00E_VisionGlimpseWhisperM.Play(MQ16_SC14_YuslanDeadREF)
    MQ16_SC14_YuslanDeadREF.SetGhost(False)
    MQ16_SC14_YuslanDeadREF.GetActorBase().SetEssential(False)
	
EndFunction

Function ResetAnimations()
	
	Debug.SendAnimationEvent(_00E_MC_TealorREF, "IdleForceDefaultState")
	Debug.SendAnimationEvent(MQ16_SC14_YuslanDeadREF, "IdleForceDefaultState")
    MQ16_SC14_YuslanDeadREF.SetGhost(False)
    MQ16_SC14_YuslanDeadREF.GetActorBase().SetEssential(False)
	
EndFunction

Function TealorKillYuslan()

    _00E_MC_TealorREF.PlayIdleWithTarget(pa_2HMKillMoveDecapSlash, MQ16_SC14_YuslanDeadREF)

    Game.TriggerScreenBlood(7)
    Utility.Wait(3)
    YuslanDeath()
    SetCurrentStageID(170)
    
EndFunction

Function YuslanDeath()
    
    MAGShockExpImod.Apply()
    GhostRedFXShader.Stop(PlayerREF)
    akTealor.SetLookAt(PlayerREF)
    MQ16_SC14_YuslanDeadREF.PlaceAtMe(ExplosionRuneShock01)
    ShockDisintegrate01FXS.Play(MQ16_SC14_YuslanDeadREF)
    MQ16_SC14_YuslanDeadREF.Disable()
    Wait(1)
    MQ16_SC14_YuslanDeadREF.AttachAshPile(DefaultAshPileDarkGhost)
    MQ16_SC14_YuslanDeadREF.GetActorBase().SetName("Yuslan Sha'Rim")
    
EndFunction

Function PlayerLooseConsciousness()

    _00E_MQ16_SC14_LooseConsciousness.ApplyCrossFade(afFadeDuration = 0.5)
    Wait(5.5)
    FadeToBlackHoldIMOD.ApplyCrossFade(afFadeDuration = 1.0)
    
EndFunction

Function DisableTealor()

    akTealor.Disable()

EndFunction

Function StartMQ17()

    MQ17.SetCurrentStageID(5)

EndFunction

;=====================================================================================
;                                        PROPERTIES                                      
;=====================================================================================

int iVisionIntenseSound
int iElevatorSound

Formlist formlistVisionShader

bool Property bGoodToGo Auto Conditional Hidden 
bool Property bPlayerInTrigger Auto Conditional Hidden
bool Property bYuslanRunToWordOfTheDead Auto Conditional Hidden
bool Property bDragonFire Auto Conditional Hidden

int Property iVisionIndexFragment Auto Conditional Hidden

_00E_MQ15_Functions Property MQ15 Auto

Quest Property MQ17 Auto

ShaderParticleGeometry Property _00E_VisionShaderParticles Auto

Message Property _00E_MQ16_sHighOnesThroughYuslan Auto
Message Property _00E_MQ16_sHighOnes Auto
Message Property _00E_MQ16_sCongealedCorpse Auto
Message Property _00E_MQ16_sFleeingChild Auto
Message Property _00E_MQ16_sFleeingWoman Auto

Actor Property akTealor Auto Hidden
Actor Property akYuslan Auto Hidden
Actor Property akCompanion Auto Hidden
Actor Property akInjuredCompanion Auto Hidden

Actor Property _00E_MC_TealorREF Auto
Actor Property _00E_MC_YuslanREF Auto
Actor Property MQ16_SC05_Tealor Auto
Actor Property MQ16_SC05_Irlanda Auto
Actor Property MQ16_SC06_BossREF Auto
Actor Property MQ16_SC06_Stage01_YuslanJesparTarget Auto
Actor Property MQ16_SC06_Stage03_ZombieGiantREF Auto
Actor Property MQ16_SC06_Stage03_Mage_01REF Auto
Actor Property MQ16_SC07_UndeadDragonREF Auto
Actor Property PlayerREF Auto
Actor Property MQ16_SC01_MotherREF02 Auto
Actor Property MQ16_SC01_ChildREF02 Auto
Actor Property MQ16_SC09_Vision_EnemyREF Auto
Actor Property MQ16_SC09_Vision_SoldierREF Auto
Actor Property MQ16_SC14_YuslanDeadREF Auto
_00E_VisionFX_NPC_SC Property MQ16_SC10_VisionKidREF Auto
_00E_VisionFX_NPC_SC Property MQ16_SC10_VisionPriestess Auto

Activator Property DefaultAshPileDarkGhost Auto

GlobalVariable Property MQ16_EchoCluesFound Auto

Topic Property MQ16_D03_VisionFragmentTopic Auto

Idle Property TG05_Knockout Auto
Idle Property TG05_GetUp Auto
Idle Property pa_2HMKillMoveDecapSlash Auto
Idle Property pa_KillMove1HMDecap Auto
Idle Property _00E_IdleCastMagicTwoHanded Auto
Idle Property IdleMagic_01 Auto
Idle Property IdleExhaustedExit Auto

Formlist Property _00E_MQ16_SC06_Stage01_Enemies Auto
Formlist Property _00E_MQ16_SC06_Stage02_Enemies Auto
Formlist Property _00E_MQ16_SC06_Stage03_Enemies Auto
Formlist Property MQ16_SC11_VisionFormlist Auto
Formlist Property MQ16_SC09_VisionNPCs Auto
Formlist Property MQ16_SC10_VisioNPCs Auto
Formlist Property MQ16_SC10_Vision_02_NPCs Auto

EffectShader Property GhostRedFXShader Auto
EffectShader Property _00E_BloodyFXShader Auto
EffectShader Property _00E_EldritchTeleportReappear Auto
EffectShader Property _00E_MQ15_EldricthDissolveFXS Auto
EffectShader Property _00E_ShatterSoulDarkFlamesShader Auto
EffectShader Property ShockDisintegrate01FXS Auto
EffectShader Property _00E_HighOnesDisintegrate Auto

Explosion Property ExplosionIllusionMassiveDark01 Auto
Explosion Property FireStormExplosion Auto
Explosion Property FireBallExp01Big Auto
Explosion Property _00E_MAGEldritchShockExplosionTeleport Auto
Explosion Property _00E_MQ16_YuslanSuicideExplosion Auto
Explosion Property ExplosionIllusionDark01 Auto
Explosion Property ExplosionRuneShock01 Auto
Explosion Property _00E_FS_MAGGoreExplosion Auto

Spell Property _00E_StaggerSelf Auto
Spell Property GhostAbilityRed Auto
Spell Property _00E_AbPosessed Auto
Spell Property _00E_MQ16_WeakenedAbSP Auto
Spell Property _00E_MQ16_RessurectSP Auto

Scene Property MQ16_SC01_Journey_01 Auto
Scene Property MQ16_SC02_Journey_02 Auto
Scene Property MQ16_SC03_Journey_03 Auto
Scene Property MQ16_SC04_Journey_04 Auto
Scene Property MQ16_SC05_HighOnes Auto
Scene Property MQ16_SC06_Assault Auto
Scene Property MQ16_SC07_DragonAttack Auto
Scene Property MQ16_SC08_Temple_01 Auto
Scene Property MQ16_SC09_Temple_02 Auto
Scene Property MQ16_SC10_Temple_03 Auto
Scene Property MQ16_SC11_Temple_04 Auto
Scene Property MQ16_SC12_Numinos Auto
Scene Property MQ16_SC13_Numinos_02 Auto
Scene Property MQ16_SC14_Temple Auto

VisualEffect Property MGTeleportInEffect Auto
VisualEffect Property MGTeleportOutEffect Auto
VisualEffect Property MS04MemoryFXBody01VFX Auto

Outfit Property _00E_MC_Yarim_Outfit Auto

ReferenceAlias Property Companion Auto

ObjectReference Property MQ16_SC03_VisionLinkerREF Auto
ObjectReference Property MQ16_SC07_CollapseCloudFXREF Auto
ObjectReference Property MQ16_SC07_DragonStrikeImpactMarkerREF Auto
ObjectReference Property MQ16_SC07_DragonStrikeImpactStonesREF Auto
ObjectReference Property MQ16_SC07_HighOnesOrb01 Auto
ObjectReference Property MQ16_SC07_HighOnesOrb02 Auto
ObjectReference Property MQ16_SC07_WallPlane004 Auto
ObjectReference Property MQ16_SC07_WallPlane003 Auto
ObjectReference Property MQ16_SC07_WallPlane002 Auto
ObjectReference Property MQ16_SC05_HighOnesEyes_01 Auto
ObjectReference Property MQ16_SC05_HighOnesEyes_02 Auto
ObjectReference Property MQ16_SC05_HighOnesEyes_03 Auto
ObjectReference Property MQ16_SC05_HighOnesEyes_04 Auto
ObjectReference Property MQ16_SC08_TealorStart Auto
ObjectReference Property MQ16_SC08_PlayerStart Auto
ObjectReference Property MQ16_SC08_YuslanStart Auto
ObjectReference Property MQ16_SC09_VisionLinkREF Auto
ObjectReference Property MQ16_SC10_VisionLinker Auto
ObjectReference Property MQ16_SC10_Vision_02_Linker Auto
ObjectReference Property MQ16_SC10_SmokeREF Auto
ObjectReference Property MQ16_SC10_WordOfTheDeadREF Auto
ObjectReference Property MQ16_SC11_WordOfTheDeadMagic Auto
ObjectReference Property MQ16_SC12_PlayerStartREF Auto
ObjectReference Property MQ16_SC12_TealorStartREF Auto
ObjectReference Property MQ16_SC12_YuslanStartREF Auto
ObjectReference Property MQ16_SC12_YuslanTeleportMarkerREF Auto
ObjectReference Property MQ16_SC13_BarrierREF Auto
ObjectReference Property MQ16_SC13_CollisionREF Auto
ObjectReference Property MQ16_SC13_NuminosREF Auto
ObjectReference Property MQ16_SC14_TealorStart Auto
ObjectReference Property MQ16_SC10_VisionActorREF Auto
ObjectReference Property MQ16_SC01_MotherStartREF Auto
ObjectReference Property MQ16_SC01_LinkMarker Auto
ObjectReference Property MQ16_SC03_KillBoxREF Auto
ObjectReference Property MQ16_SC05_IllusionTealorStartMarker Auto
ObjectReference Property MQ16_SC05_IllusionIrlandaStartMarker Auto
ObjectReference Property MQ16_SC04_Corpse01REF Auto
ObjectReference Property MQ16_SC04_Corpse02REF Auto
ObjectReference Property MQ16_SC04_Corpse03REF Auto
ObjectReference Property MQ16_SC04_Corpse04REF Auto
ObjectReference Property MQ16_SC06_ProjectileSpawn Auto
ObjectReference Property MQ16_SC09_VisionNPCLinkREF Auto
ObjectReference Property MQ16_SC14_PlayerWoundedMarker Auto
ObjectReference Property MQ16_SC14_PlayerWoundedMarkerFailsave Auto
ObjectReference Property MQ16S_SC14_YuslanStartMarker Auto
ObjectReference Property MQ16_SC14_YuslanBedRoll Auto
ObjectReference Property MQ16_SC03_collisionREF Auto
ObjectReference Property MQ16_SC03_VisionVoice Auto

SoundCategory Property AudioCategoryMuteSubmerged Auto

Light Property _00E_MQ16_HighOnesRedLight Auto
Light Property Torch01RedDesat Auto
Light Property Torch01 Auto

Sound Property QSTTG05ArrowKnockOut2D Auto
Sound Property _00E_A1_RocksolidOutM Auto
Sound Property NPCDragonTakeoffFX Auto
Sound Property NPCDragonWingFlapTakeoff Auto
Sound Property NPCDragonSkeletalResurrectionRumble01 Auto
Sound Property NPCDragonSkeletalResurrectionRoarAM Auto
Sound Property NPCDragonSkeletalResurrectionRoarBM Auto
Sound Property FXFireOut Auto
Sound Property MAGConjureBoundWeaponAppearM Auto
Sound Property _00E_AMB_Vision_SoundLPM Auto
Sound Property _00E_VisionGlimpseWhisperM Auto
Sound Property MAGVampireSunlight Auto
Sound Property MAGIllusionCharm Auto
Sound Property _00E_MQ16_EchoCleansingM Auto
Sound Property _00E_Ability_ShadowrunTeleportSoundM Auto
Sound Property _00E_MAGEldritchFireSS1M Auto
Sound Property QSTDA10Rumble Auto
Sound Property WPNImpactBlade2HandVsFlesh Auto
Sound Property _00E_MQ16_SC01_ScreamM Auto
Sound Property FXExplosionCatapultNearM Auto
Sound Property _00E_MQ11c_RyneusTransformSoundM Auto
Sound Property _00E_MQ16_BattlefieldVisionM Auto
Sound Property AMBRumbleShake Auto

Message Property _00E_MQ16_Temple_Thoughts_01 Auto

ImpactDataSet Property BloodSprayImpactSetRed Auto

ImageSpaceModifier Property FadeToBlackHoldImod Auto
ImageSpaceModifier Property MAGFireBallExpDragonImod Auto
ImageSpaceModifier Property _00E_MQ02_WakeUp Auto
ImageSpaceModifier Property _00E_MQ16_VisionIMOD Auto
ImageSpaceModifier Property _00E_MQ16_EchoCleansingIMOD Auto
ImageSpaceModifier Property FadeToWhiteHoldImod Auto
ImageSpaceModifier Property _00E_MQ16_SC13_YuslanSuicideIMOD Auto
ImageSpaceModifier Property _00E_MQ16_SC11_VisionCleansingBuildUpIMOD Auto
ImageSpaceModifier Property _00E_MQ11c_DreamCollapseIMOD Auto
ImageSpaceModifier Property _00E_WakeUp Auto
ImageSpaceModifier Property MAGShockExpImod Auto
ImageSpaceModifier Property _00E_MQ16_HeadacheLoopImod Auto
ImageSpaceModifier Property _00E_MQ16_SC14_LooseConsciousness Auto

MusicType Property _00E_Music_Special_Zyklus_OneSelection Auto
MusicType Property _00E_Music_Special_Zyklus_Loop Auto
MusicType Property _00E_Music_Combat_Epic Auto
MusicType Property _00E_SilenceTransitionHighPriority Auto
MusicType Property _00E_Music_Special_MQ16_Numinos Auto

;=====================================================================================
;                 ZP (Zenderal - MQ16 Yuslan Kneel Fix): SC04 kneel watchdog
;=====================================================================================
; Scene MQ16_SC04_Journey_04 (147193): after Yuslan's "Good question." (action 4, phase 2), phase 3 waits
; until Yuslan is in furniture state Sit. His package MQ16_SC04_SitTarget (1471B7) kneels him at the
; KneelingMarker ref 1471B6 by the fourth corpse. A player's Yuslan never knelt and the quest stopped there
; (report 2026-11-14); a console disable/enable of Yuslan freed it. DisableFollower_SC04 (phase 0's end)
; starts this watchdog. It times phases 3-4 (action 4 done, Yuslan's next line, action 20, not yet done),
; logs Yuslan's state as [ZP MQ16 kneel] and, if he has not knelt, nudges him one step at a time, up to
; the disable/enable that worked. Non-property variables only: no property is added to SureAI's script.

int iZPPhaseSeconds     ; seconds spent in phases 3-4
int iZPUnseatedSeconds  ; of those, seconds Yuslan was not sitting
int iZPStep
bool bZPSeatedReset
bool bZPInTick

Function ZP_StartKneelWatch()

	iZPPhaseSeconds = 0
	iZPUnseatedSeconds = 0
	iZPStep = 0
	bZPSeatedReset = False
	bZPInTick = False
	Debug.Trace("[ZP MQ16 kneel] watch started (SC04 phase 0 done)")
	RegisterForSingleUpdate(1.0)

EndFunction

Event OnUpdate()

	If bZPInTick
		; a step is waiting on a latent call: keep the chain alive, do nothing else
		RegisterForSingleUpdate(1.0)
		Return
	EndIf

	If !MQ16_SC04_Journey_04.IsPlaying() || MQ16_SC04_Journey_04.IsActionComplete(20) || GetCurrentStageID() >= 60
		Debug.Trace("[ZP MQ16 kneel] watch ended: playing=" + MQ16_SC04_Journey_04.IsPlaying() + " yuslanLine=" + MQ16_SC04_Journey_04.IsActionComplete(20) + " stage=" + GetCurrentStageID() + " | phases 3-4 " + iZPPhaseSeconds + " s, not kneeling " + iZPUnseatedSeconds + " s")
		Return
	EndIf

	; next tick first: nothing below may end the watch
	RegisterForSingleUpdate(1.0)

	If MQ16_SC04_Journey_04.IsActionComplete(4)
		bZPInTick = True
		ZP_KneelTick()
		bZPInTick = False
	EndIf

EndEvent

Function ZP_KneelTick()

	Actor akY = _00E_MC_YuslanREF
	iZPPhaseSeconds += 1
	bool bSeated = akY.GetSitState() == 3
	If !bSeated
		iZPUnseatedSeconds += 1
	EndIf

	If iZPPhaseSeconds == 1
		ZP_KneelLog("phase 3 (after 'Good question.')")
	EndIf

	If !bSeated
		If iZPStep == 0 && iZPUnseatedSeconds >= 12
			iZPStep = 1
			ZP_KneelLog("not kneeling after 12 s: EvaluatePackage")
			akY.EvaluatePackage()
		ElseIf iZPStep == 1 && iZPUnseatedSeconds >= 20
			iZPStep = 2
			ZP_KneelLog("not kneeling after 20 s: sheathe, IdleForceDefaultState, EvaluatePackage")
			If akY.IsWeaponDrawn()
				akY.SheatheWeapon()
			EndIf
			Debug.SendAnimationEvent(akY, "IdleForceDefaultState")
			akY.EvaluatePackage()
		ElseIf iZPStep == 2 && iZPUnseatedSeconds >= 30
			iZPStep = 3
			ZP_KneelLog("not kneeling after 30 s: disable/enable (the console fix)")
			ZP_ResetYuslan()
			ZP_KneelLog("after disable/enable")
		ElseIf iZPStep == 3 && iZPUnseatedSeconds >= 45
			iZPStep = 4
			ZP_KneelLog("not kneeling after 45 s: MoveTo the kneel marker and activate it")
			ObjectReference akKneel = Game.GetForm(0x001471B6) as ObjectReference
			If akKneel
				akY.MoveTo(akKneel)
				akKneel.Activate(akY)
			EndIf
			akY.EvaluatePackage()
		ElseIf iZPStep == 4 && iZPUnseatedSeconds >= 60
			iZPStep = 5
			ZP_KneelLog("not kneeling after 60 s: disable/enable again")
			ZP_ResetYuslan()
			ZP_KneelLog("after disable/enable")
		ElseIf iZPStep >= 5 && iZPUnseatedSeconds % 30 == 0
			ZP_KneelLog("STALL: still not kneeling. Console: prid 102DED, disable, enable")
		EndIf
	ElseIf !bZPSeatedReset && iZPPhaseSeconds - iZPUnseatedSeconds >= 40
		; his next line takes ~6 s once he kneels: 40 s kneeling with no line = the scene does not see him seated
		bZPSeatedReset = True
		ZP_KneelLog("kneeling 40 s but the scene has not moved on: disable/enable")
		ZP_ResetYuslan()
		ZP_KneelLog("after disable/enable")
	EndIf

EndFunction

Function ZP_ResetYuslan()

	Actor akY = _00E_MC_YuslanREF
	akY.Disable()
	Utility.Wait(0.5)
	akY.Enable()
	akY.EvaluatePackage()

EndFunction

Function ZP_KneelLog(string sWhat)

	Actor akY = _00E_MC_YuslanREF
	ObjectReference akKneel = Game.GetForm(0x001471B6) as ObjectReference
	Actor akCalia = (GetAlias(1) as ReferenceAlias).GetActorRef()
	string s = "[ZP MQ16 kneel] " + sWhat + " | t=" + iZPPhaseSeconds + " notKneeling=" + iZPUnseatedSeconds
	s += " | Yuslan sit=" + akY.GetSitState() + " pkg=" + akY.GetCurrentPackage() + " disabled=" + akY.IsDisabled() + " 3D=" + akY.Is3DLoaded()
	s += " pos=" + akY.GetPositionX() + "," + akY.GetPositionY() + "," + akY.GetPositionZ()
	If akKneel
		s += " | to marker: Yuslan=" + akY.GetDistance(akKneel) + " player=" + PlayerREF.GetDistance(akKneel) + " Tealor=" + _00E_MC_TealorREF.GetDistance(akKneel)
		If akCalia
			s += " Calia=" + akCalia.GetDistance(akKneel)
		EndIf
		If akCompanion
			s += " companion=" + akCompanion.GetDistance(akKneel)
		EndIf
	EndIf
	s += " | weaponDrawn=" + akY.IsWeaponDrawn() + " combat=" + akY.GetCombatState() + " bleedout=" + akY.IsBleedingOut() + " unconscious=" + akY.IsUnconscious() + " dialogue=" + akY.IsInDialogueWithPlayer()
	s += " R=" + akY.GetEquippedObject(1) + " L=" + akY.GetEquippedObject(0)
	s += " | graph animDriven=" + akY.GetAnimationVariableBool("bAnimationDriven") + " equipping=" + akY.GetAnimationVariableBool("IsEquipping") + " unequipping=" + akY.GetAnimationVariableBool("IsUnequipping") + " stagger=" + akY.GetAnimationVariableBool("IsStaggering") + " block=" + akY.GetAnimationVariableBool("IsBlocking") + " jump=" + akY.GetAnimationVariableBool("bInJumpState") + " synced=" + akY.GetAnimationVariableBool("bIsSynced") + " iState=" + akY.GetAnimationVariableInt("iState")
	s += " | scene playing=" + MQ16_SC04_Journey_04.IsPlaying() + " a4=" + MQ16_SC04_Journey_04.IsActionComplete(4) + " a19=" + MQ16_SC04_Journey_04.IsActionComplete(19) + " a20=" + MQ16_SC04_Journey_04.IsActionComplete(20)
	Debug.Trace(s)

EndFunction
