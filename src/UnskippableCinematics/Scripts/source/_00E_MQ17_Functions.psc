Scriptname _00E_MQ17_Functions extends Quest Conditional

Import Utility

int function _GetScriptVersion() Global
    return 1
endFunction

;=====================================================================================
;              							FUNCTIONS                    					 
;=====================================================================================

Function SetUp()

	MQ06_CaliaPointChronikumMarkerDUPLICATE001.Disable()

	if MQ16.akCompanion == _00E_MC_CaliaREF 
		MQ17_JesparFinalCompanion.SetValueInt(0)
		bIsCaliaCompanion = True
	Else
		MQ17_JesparFinalCompanion.SetValueInt(1)
		bIsCaliaCompanion = False
	EndIf

	if bIsCaliaCompanion
		akCompanion = _00E_MC_CaliaREF
	Else
		akCompanion = _00E_MC_JesparREF
	EndIf
	
	Companion.ForceRefTo(akCompanion)
	
	Game.DisablePlayerControls(true, true, true, true, true, true, true)
	Game.ForceFirstPerson()
	FadeToBlackHoldIMOD.Apply()
	PlayerREF.MoveTo(MQ17_SC01_PlayerWakeUpMarkerFailsave)
	PlayerREF.PlayIdle(TG05_Knockout)
	_00E_MC_VeiledWomanREF.Enable()
	_00E_MC_VeiledWomanREF.MoveTo(MQ17_SC01_VeiledWomanStartMarkerFailsave)
	_00E_MC_VeiledWomanREF.SetAlpha(0.9)

	MQ17_SC01_PlayerWakesUpSC.ForceStart()
	
EndFunction

Function VeiledWomanAppears()

	Wait(2)
	MAGRestorationFFFire.Play(PlayerREF)
	_00E_MC_VeiledWomanREF.SetAlpha(0.9)
	FadeToBlackHoldIMOD.Remove()
	_00E_MQ17_SC01_VeiledWomanFade.Apply()

EndFunction

Function FadeToBlack()

	FadeToBlackHoldIMOD.ApplyCrossFade(afFadeDuration = 0.25)

EndFunction

Function WakeUp()

	_00E_MC_VeiledWomanREF.Disable()
	_00E_MC_TealorREF.Disable()
	MQ17_SC01_RailREF.Disable()
	MQ17_SC01_PortalDoorFailsave.Enable()
	iPortalSound = QSTSovengardePortalOn2DLPM.Play(MQ17_SC01_PortalDoorFailsave)	
	_00E_MQ17_SC01_PlayerAwakeIMOD.ApplyCrossFade(afFadeDuration = 2.0)
	PlayerREF.PlayIdle(TG05_GetUp)
	PlayerREF.DamageActorValue("Health", (PlayerREF.GetActorValue("Health")*0.7))
	Wait(2)
	MQ17_SC01_PortalDoorFailsave.PlayAnimation("playAnim02")
	Wait(2)
	Game.EnablePlayerControls()
	SetObjectiveDisplayed(5)
	
EndFunction

Function StartVision01()

	MQ17_SC01_PortalDoorFailsave.Enable()
	MQ17_SC01_PortalDoorFailsave.PlayAnimation("playAnim02")
	
	If MQ16_SC10_VisionActorREF.IsDisabled()
		MQ16_SC10_VisionActorREF.Enable()
	EndIf
	
	bIsVisionPlaying = True
	
	_00E_MQ16_VisionIMOD.Apply()
	_00E_PlayerFunctions.GetVisionControl().VisionEffectNoTimestop(MQ17_SC02_VisionsInvolvedList, emptyFormlist)
	
	MQ17_SC02_Vision_01_SC.ForceStart()

	MQ16_SC10_VisionActorREF.Say(MQ17_D01_VisionBranchTopic)
	
EndFunction

Function StartVision02()

	MQ17_SC01_PortalDoorFailsave.PlayAnimation("playAnim02")

	bIsVisionPlaying = True

	_00E_MQ16_VisionIMOD.Apply()
	Wait(0.1)
	_00E_PlayerFunctions.GetVisionControl().VisionEffectNoTimestop(MQ17_SC02_VisionsInvolvedList, emptyFormlist)
	
	MQ17_SC02_Vision_02_SC.ForceStart()
			
	If MQ16_SC10_VisionActorREF.IsDisabled()
		MQ16_SC10_VisionActorREF.Enable()
	EndIf
	
	MQ16_SC10_VisionActorREF.Say(MQ17_D01_VisionBranchTopic)
	
EndFunction

Function StartVision03()

	bIsVisionPlaying = True
	_00E_MQ16_VisionIMOD.Apply()
	_00E_PlayerFunctions.GetVisionControl().VisionEffectNoTimestop(MQ17_SC02_VisionsInvolvedList, emptyFormlist)	
	Wait(0.25)

	MQ17_SC02_Vision_03_SC.ForceStart()
					
	If MQ16_SC10_VisionActorREF.IsDisabled()
		MQ16_SC10_VisionActorREF.Enable()
	EndIf
	
	MQ16_SC10_VisionActorREF.Say(MQ17_D01_VisionBranchTopic)

EndFunction

Function StopVision()

	_00E_PlayerFunctions.GetVisionControl().VisionEffectNoTimestopStop(MQ17_SC02_VisionsInvolvedList, emptyFormlist)
	Sound.StopInstance(iVisionIntenseSound)
	
	If MQ17_SC02_PyreanChroniclerREF.IsEnabled()
		MQ17_SC02_PyreanChroniclerREF.Disable()
	EndIf
			
	If MQ17_SC02_PyreanOfficerREF.IsEnabled()
		MQ17_SC02_PyreanOfficerREF.Disable()
	EndIf
	
	_00E_MQ16_VisionIMOD.Remove()
	MQ16_SC10_VisionActorREF.Disable()
	
	bIsVisionPlaying = False
	
EndFunction

Function TeleportPlayer()

	_00E_A2_Ghostwalk_TeleportDoneSound.Play(PlayerREF)
	PlayerREF.MoveTo(MQ17_SC02_PlayerStart)
	Game.ForceThirdPerson()
	Game.DisablePlayerControls()
	Game.ShakeCamera(afStrength = 0.2)
	Debug.SendAnimationEvent(PlayerREF, "IdleWebEnterInstant")
	TimeFadeOut01FXS.Stop(PlayerREF)
	TimeFadeIn01FXS.Play(PlayerREF)
	PlayerREF.setActorValue("Variable03", 5)
	Wait(0.5)
	PlayerREF.playidle(WebIdleExit)
	Wait(2)
	TimeFadeIn01FXS.Stop(PlayerREF)
	PlayerREF.SetActorValue("Variable03", 0)
	Debug.SendAnimationEvent(PlayerREF, "IdleForceDefaultState")
	Game.EnablePlayerControls()
	
EndFunction

Function StartSC03()

	MQ17_SC02_BlackGuardianLightLinker.Enable()
	QSTAlduinDeathExplosionA.Play(MQ17_SC07_BlackGuardianVoice)
	int iTurnOnSound = _00E_AltIshmartepElectroShotSound.Play(MQ17_SC02_BlackGuardianLightLinker)
	Sound.SetInstanceVolume(iTurnOnSound, 5.0)
	MQ17_SC03_BlackGuardian_01.ForceStart()
	
EndFunction

Function BlackGuardianEngageDialogue()

	MQ17_SC07_BlackGuardianVoice.Activate(PlayerREF)

	Wait(3)
	
	If !(MQ17_SC07_BlackGuardianVoice.IsInDialogueWithPlayer())
		MQ17_SC07_BlackGuardianVoice.Activate(PlayerREF)
	EndIf
	
EndFunction

Function StartExplanationVideo01()
	
	MQ17_SC03_BlackGuardian_01.Stop()
	If _00E_VideoSkip.GetValueInt() == 0 && EnderalFunctions.VideoSupport()
		FadeToBlackAndBackIMOD.apply()
		Utility.Wait(3.2)
		; ZP: not interruptible - a key press ended it at once
		Game.PlayBink("MQ17BlackGuardian.bik", false)
		Wait(2)
	EndIf
	SetCurrentStageID(40)

EndFunction

Function StartSC04()

	MQ17_SC04_BlackGuardian_02.ForceStart()

EndFunction

Function StartExplanationVideo02()

	MQ17_SC04_BlackGuardian_02.Stop()
	Wait(1)
	SetCurrentStageID(50)

EndFunction

Function StartSC05()

	MQ17_SC05_BlackGuardian_03.ForceStart()

EndFunction

Function UnblockButton()

	MQ17_SC05_BlackGuardianButton.BlockActivation(False)

EndFunction

Function TrapPlayer()
	
	_00E_EquipControl.SheatheWeapon(PlayerREF)
	_00E_Func_AIWalk.PlayerAIWalk(False)
	Game.ForceThirdPerson()
	Game.DisablePlayerControls(True, True, True, True, True, True, True)
	MQ17_SC06_BlackGuardianTriesToTrapPlayer.ForceStart()
	
EndFunction

Function PlayTrappedFX()
	_00E_Music_Special_MQ17_BlackGuardian.remove()
	Game.EnablePlayerControls()
	Game.DisablePlayerControls(True, True, True, False, True, True, True)
	_00E_PlayerFunctions.GetSoundControl().RemoveSilence()
	_00E_Music_Combat_Epic.Add()
	QSTDA10Rumble.Play(PlayerREF)
	MQ17_SC06_AbsorbLightREF.Enable()
	MQ17_SC06_AbsorbLightREFPlayer.Enable()
	MQ17_SC06_BlackGuardianHeartREF.PlayGamebryoAnimation("AnimTrans01")
	MQ17_SC06_BlackGuardianHeartREF.PlayGamebryoAnimation("AnimIdle02")
	AbsorbCastVFX01.Play(MQ17_SC06_BlackGuardianHeartREF, akFacingObject = PlayerREF)
	AbsorbTargetVFX01Orange.Play(PlayerREF, akFacingObject = MQ17_SC06_BlackGuardianHeartREF)
	MQ17_SC06_PillarREF.playAnimation("playanim01")
	Wait(1)
	iHeartActiveSound = QSTUstengravRumble2DLPM.Play(MQ17_SC06_BlackGuardianHeartREF)
	iHeartActiveSound02 = QSTDA02ShrineActivateLPMM.Play(PlayerREF)
	Sound.SetInstanceVolume(iHeartActiveSound, 5.0)
	Sound.SetInstanceVolume(iHeartActiveSound02, 5.0)
	_00E_MQ17_SC06_TransformConsciousnessIMOD.Apply() 
	
EndFunction

Function TogglePostCamera()

	MQ17_SC06_CameraREF.Enable()
	MQ17_SC06_CameraREF.MoveTo(PlayerREF)
	Game.SetCameraTarget(MQ17_SC06_CameraREF)
	MQ17_SC06_CameraREF.SetPlayerControls(False)
  	MQ17_SC06_CameraREF.EnableAI(False)
  	MQ17_SC06_CameraREF.EnableAI(True)
	MQ17_SC06_CameraREF.SetAllowFlying(True)
	Game.ForceThirdPerson()
	Wait(3)
	MQ17_SC06_CameraREF.TranslateToREF(MQ17_SC06_CameraPos, 500.0, 500.0)
	
EndFunction

Function CompanionCastSpell()

	JesparNoCombatComments.SetValueInt(1)
	_00E_MQ17_SC06_FlamingArrowSP.Cast(akCompanion, MQ17_SC06_FalmerKeys)

EndFunction

Function SpawnCompanion()

	akCompanion.AddItem(_00E_MQ11a_SC12_FireArrows, 5)
	akCompanion.AddItem(_02E_11Eichenbogen, 1)
	akCompanion.EquipItem(_02E_11Eichenbogen, True)
	akCompanion.EquipItem(_00E_MQ11a_SC12_FireArrows, True)
	
	If akCompanion.IsDisabled()
		akCompanion.Enable()
	EndIf

	akCompanion.MoveTo(MQ17_SC06_CompanionSpawnMarker)
	
EndFunction

Function ExplodeButton()

	_00E_MQ17_BlackGuardianScreamsM.Play(MQ17_SC06_BlackGuardianHeartREF)
	_00E_MQ17_SC06_TransformConsciousnessIMOD.Remove()
	_00E_MQ17_SC06_FireArrowImpactIMOD.Apply()
	Game.DisablePlayerControls()
	Game.ShakeCamera()
	NPCDwarvenCenturionDeathM.Play(MQ17_SC06_BlackGuardianHeartREF)
	Game.SetCameraTarget(PlayerREF)
	MAGShockExpImod.ApplyCrossFade(afFadeDuration = 0.1)
	_00E_MQ17_SC06_TransformConsciousnessIMOD.Remove()
	MQ17_SC06_CameraREF.SetPlayerControls(False)
	_00E_MQ17_SC06_FireArrowImpactIMOD.Apply()
	PlayerREF.MoveTo(MQ17_SC06_PillarExitMarker)
	Wait(0.25)
	Debug.SendAnimationEvent(PlayerREF, "IdleWebEnterInstant")
	MQ17_SC02_BlackGuardianLightLinker.Disable()
	MQ17_SC06_AbsorbLightREF.Disable()
	MQ17_SC06_AbsorbLightREFPlayer.Disable()
	MQ17_SC05_BlackGuardianButton.PlaceAtMe(ExplosionRuneShock02)
	MQ17_SC06_BlackGuardianHeartREF.PlaceAtMe(ExplosionRuneShock02)
	Sound.StopInstance(iHeartActiveSound)
	Sound.StopInstance(iHeartActiveSound02)
	AbsorbCastVFX01.Stop(MQ17_SC06_BlackGuardianHeartREF)
	AbsorbTargetVFX01Orange.Stop(PlayerREF)
	Wait(0.25)
	PlayerREF.playidle(WebIdleExit)
	Wait(0.25)
	Game.ShakeCamera(afStrength = 0.25)
	PlayerREF.PlaceAtMe(_00E_FXDustExplosionSmaller)
	Wait(1)
	MQ17_SC06_CameraREF.Disable()
	Game.EnablePlayerControls()
	_00E_CameraControl.UnlockVanityCamera() 
	_00E_Func_AIWalk.PlayerAIWalkStop()
	Debug.SendAnimationEvent(PlayerREF, "IdleForceDefaultState")
	
EndFunction

Function StartFight()

	if MQ17_SC07_BlackGuardianVoice.IsDisabled()
		MQ17_SC07_BlackGuardianVoice.Enable()
	EndIf

	Game.SetHudCartMode(False)
	MQ17_Generator_Left_REF003.SetMotionType(4)
	MQ17_Generator_Right_REF003.SetMotionType(4)
	_00E_EquipControl.SheatheWeapon(akCompanion)
	akCompanion.UnequipItem(_02E_11Eichenbogen)
	akCompanion.RemoveItem(_02E_11Eichenbogen)
	akCompanion.RemoveItem(_00E_MQ11a_SC12_FireArrows)

	; SE: Prevents NPC from using only fists
	akCompanion.ResetInventory()

	MQ17_SC07_BlackGuardianFight.ForceStart()
	CompanionIsTalking.SetValueInt(0)
	MAGFireExpertHitImod.Apply()
	MQ16_SC07_FightLinker.Enable()
	MQ17_SC06_AbsorbLightREF.Enable()
	Game.ShakeCamera(afStrength = 1.0)
	akCompanion.KnockAreaEffect(1, 512)
	;_00E_MAGFXFireOilIgniteLow.Play(MQ17_SC07_Fire_001)
	;_00E_MAGFXFireOilIgniteLow.Play(MQ17_SC07_Fire_002)
	MQ17_SC06_BlackGuardianHeartREF.PlaceAtMe(_00E_A2_StarlingdummyDetExp)
	MQ17_SC07_Fire_001.PlaceAtMe(_00E_A2_StarlingdummyDetExp)
	MQ17_SC07_Fire_002.PlaceAtMe(_00E_A2_StarlingdummyDetExp)
	MQ17_SC02_BlackGuardianLightLinker.Enable()
	FXExplosionFirestormNearM.Play(PlayerREF)
	
EndFunction

Function BeginFight()

	CompanionIsTalking.SetValueInt(0)
	MQ17_CombatControllerREF.InitializeFight()
	_00E_Func_SetNPCAsCompanion.SetNPCAsCompanion(akCompanion, True, 750, 800, 300)

EndFunction

Function DestroyBlackGuardian()

	MQ17_CombatControllerREF.KillAllLemmings()
	MQ17_SC07_BlackGuardianVoice.Say(MQ17_D04_FinalFightScream)
	Game.RequestAutoSave()
	Wait(1)
	_00E_MQ17_SC08_BlackGuardianCollapseIMOD.Apply()
	int iShockSound = MAGShockFFFireM.Play(MQ17_SC08_SoundMarker)
	Sound.SetInstanceVolume(iShockSound, 5.0)
	MQ17_SC06_BlackGuardianHeartREF.PlaceAtMe(ExplosionRuneShock02)
	Game.ShakeCamera(afStrength = 0.75)
	Wait(2)
	MQ17_SC06_BlackGuardianHeartREF.PlaceAtMe(DA16SkullAreaExplosion)
	MQ17_SC06_BlackGuardianHeartREF.PlayAnimation("playAnim02")
	_00E_MQ13c_TurretChargeSoundM.Play(MQ17_SC07_BlackGuardianVoice)
	Game.ShakeCamera(afStrength = 0.5, afDuration = 2.0)
	Wait(2)
	Game.ShakeCamera(afStrength = 0.1)
	MQ17_SC06_BlackGuardianHeartREF.Disable()
	MQ17_SC08_Death_Right_001.PlaceAtMe(_00E_FireballExpSmallHarmless)
	MQ17_SC08_Death_Left_001.PlaceAtMe(_00E_FireballExpSmallHarmless)
	
	if MQ17_BlackGuardianIsTalking.GetValueInt() == 1
		MQ17_BlackGuardianIsTalking.SetValueInt(0)
	EndIf
	
	Wait(0.3)
	Game.ShakeCamera(afStrength = 0.25)
	MQ17_SC08_Death_Right_002.PlaceAtMe(_00E_FireballExpSmallHarmless)
	MQ17_SC08_Death_Left_002.PlaceAtMe(_00E_FireballExpSmallHarmless)
	Wait(0.3)
	Game.ShakeCamera(afStrength = 0.5)
	MQ17_SC08_Death_Right_003.PlaceAtMe(_00E_FireballExpSmallHarmless)
	MQ17_SC08_Death_Left_003.PlaceAtMe(_00E_FireballExpSmallHarmless)
	Wait(0.3)
	Game.ShakeCamera(afStrength = 0.75)
	MQ17_SC08_Death_Right_004.PlaceAtMe(_00E_FireballExpSmallHarmless)
	MQ17_SC08_Death_Left_004.PlaceAtMe(_00E_FireballExpSmallHarmless)
	Wait(0.3)
	alduinExplosionFlashImod.ApplyCrossFade(afFadeDuration = 0.1)
	FXExplosionCatapultNearM.Play(MQ17_SC08_SoundMarker)
	Game.ShakeCamera(afStrength = 1.0)
	MAGFireExpertHitImod.Apply()
	MQ17_SC08_LightRefREF.Enable()
	MQ17_SC07_BlackGuardianJaw_Cast001.PlaceAtMe(_00E_FireballExpSmallHarmless)
	MQ17_SC08_Death_Chest.PlaceAtMe(_00E_A2_StarlingdummyDetExp)
	MQ17_SC08_Death_Chest.PlaceAtMe(_00E_HarmlessFireExplosion)
	TRPDwemerPistonOutM.Play(MQ17_SC08_SoundMarker)
	ObjectReference jawHavok = MQ17_SC07_BlackGuardianJaw_REF002.PlaceAtMe(_00E_MQ17_BlackGuardianJaw)
	
	if jawHavok != None
		jawHavok.SetScale(2)
	EndIf
	
	MQ17_SC07_BlackGuardianJaw_REF002.Disable()
	MQ17_SC07_FireFXREF003.Disable()
	MQ17_SC07_MouthLightREF001.Disable()
	akCompanion.KnockAreaEffect(1, 2048)
	MQ17_SC06_AbsorbLightREF.Disable()
	MQ17_SC02_BlackGuardianLightLinker.Disable()
	Wait(0.75)
	MQ17_SC08_DeathSmoke.Enable()
	SetCurrentStageID(90)
    SetObjectiveDisplayed(18)
	_00E_Func_SetNPCAsCompanion.SetNPCAsCompanion(akCompanion, False)

	Steam.UnlockAchievement("END_BLACK_GUARDIAN_01")
	
EndFunction

Function HeadacheCompanion()

	_00E_HorrorPulseFarSingleM.Play(akCompanion)
	_00E_Purge_ShaderFX.Play(akCompanion)
	Wait(2)
	_00E_Purge_ShaderFX.Stop(akCompanion)

EndFunction

Function StartSC08()

	_00E_SilenceAbruptHighPriority.Add()
	FadeToBlackImod.Apply()
	Wait(2)
	FadeToBlackHoldImod.ApplyCrossFade(afFadeDuration = 1.0)
	
	If PlayerREF.GetEquippedShield() != None
		PlayerREF.UnequipItem(PlayerREF.GetEquippedShield(), false, true)
	EndIf	
	PlayerREF.EquipItem(_00E_InvisibleHelmet_Armor, false, true)
	Utility.Wait(0.1)
	PlayerREF.RemoveItem(_00E_InvisibleHelmet_Armor, 1, true)
	Wait(1)
	akCompanion.MoveTo(MQ17_SC08_CompanionMarker)
	PlayerREF.MoveTo(MQ17_SC08_PlayerMarker01)
	MQ17_EntranceDoorREF.BlockActivation(True)
	Game.DisablePlayerControls()
	MQ17_SC08_PreCleansing.ForceStart()
	FadeToBlackBackImod.ApplyCrossFade(afFadeDuration = 1.0)
	Game.RequestAutoSave()
    SetObjectiveCompleted(18)
	
EndFunction

Function PlayKiss()

	_00E_EquipControl.SheatheWeapon(PlayerREF)
	
	PlayerREF.UnequipItem(PlayerREF.GetEquippedShield())
	
	_FS_TheriantrophistControlQuest.TransformBackIfTransformed()
	

	if akCompanion == _00E_MC_JesparREF 
	
		Debug.ToggleMenus()
		Debug.ToggleCollisions()
		AudioCategoryMAG.SetVolume(0.7)
		AudioCategorySFX.SetVolume(0.7)
		Game.SetPlayerAIDriven(True)
		Game.DisablePlayerControls(true, true, true, false, true, true, true, true)
		Game.ForceThirdPerson()
		Utility.Wait(0.5)
		
		If PlayerREF.GetActorBase().GetSex() == 0
			PlayerREF.PlayIdleWithTarget(pa_Idle_Kiss_MaleMale, _00E_MC_JesparREF)
		Else
			_00E_MC_JesparREF.PlayIdleWithTarget(pa_Idle_Kiss_MaleFemale, PlayerREF)
		EndIf
		
		Utility.Wait(0.5)
		
		PlayerREF.SetUnconscious(True)
		_00E_MC_JesparREF.SetUnconscious(True)
		PlayerREF.AddSpell(_00E_Game_abSlowTime, false)
		
	Else
		AudioCategoryMAG.SetVolume(0.7)
		AudioCategorySFX.SetVolume(0.7)
		Debug.ToggleMenus()
		Debug.ToggleCollisions()
		_00E_CameraControl.LockVanityCamera()
		Game.SetPlayerAIDriven(True)
		Game.DisablePlayerControls(true, true, true, false, true, true, true, true)
		Game.ForceThirdPerson()
		Utility.Wait(0.5)
		
		If PlayerREF.GetActorBase().GetSex() == 0
			PlayerREF.PlayIdleWithTarget(pa_Idle_Kiss_FemaleMale, _00E_MC_CaliaREF)
		Else
			PlayerREF.PlayIdleWithTarget(pa_Idle_Kiss_FemaleFemale, _00E_MC_CaliaREF)
		EndIf
		
		Utility.Wait(0.5)
		PlayerREF.SetUnconscious(True)
		_00E_MC_CaliaREF.SetUnconscious(True)
		PlayerREF.AddSpell(_00E_Game_abSlowTime, false)
	EndIf

	Wait(8)
	
	FadeToBlackImod.Apply()
	Wait(2)
	FadeToBlackHoldIMOD.ApplyCrossFade(1)
	Wait(1)
	
EndFunction

Function EndKiss()

	AudioCategoryMAG.SetVolume(1.0)
	AudioCategorySFX.SetVolume(1.0)
	PlayerREF.RemoveSpell(_00E_Game_abSlowTime)
	_00E_Func_AIWalk.PlayerAIWalkStop()
	akCompanion.SetUnconscious(False)
	PlayerREF.SetUnconscious(False)
	Debug.ToggleMenus()
	Debug.ToggleCollisions()
	; GameHour.SetValue(13.0)
	_00E_CameraControl.UnlockVanityCamera()
	_00E_Func_RefreshFace.RefreshFace()

EndFunction

Function FadeOutNormal()

	FadeToBlackImod.Apply()
	Wait(2)
	FadeToBlackHoldIMOD.ApplyCrossFade(1)
	Wait(1)
	_00E_SilenceAbruptHighPriority.Add()
	
EndFunction

Function StartSC09()

	Self.CompleteAllObjectives()
	
	akCompanion.MoveTo(_00E_NPCDumpMarker)
	
	If akCompanion.GetParentCell() == PlayerREF.GetParentCell()
		akCompanion.MoveTo(MQ17_SC06_PillarExitMarker)
	EndIf
	
	MQ14_SC04_SmokeREF.Disable()
	
	DisableAllNPCs()
	
	int iIndex = MQ17_KeepersToDisable.GetSize() - 1
	
	while iIndex >= 0
		ObjectReference akActorToDisable = MQ17_KeepersToDisable.GetAt(iIndex) as ObjectReference
		akActorToDisable.Disable()
		iIndex -= 1
	endwhile
		
	BlockAllDoors()
	
	If LeuchtfeuerSwitcher.IsDisabled()
		LeuchtfeuerSwitcher.Enable()
	EndIf
	
	If MQ14_SC04_BarrierREF.IsEnabled()
		MQ14_SC04_BarrierREF.Disable()
	EndIf
	
	MQ12a_SC3_BlackStone03.Enable()
	MQ12a_SC1_BlackStone01.Enable()
	MQ12a_SC1_BlackStone02.Enable()

	If akCompanion == _00E_MC_CaliaREF
		MQ17_SC09_CapsuleActivatorREF_Calia.Enable()
		_00E_MC_Jespar_Purge_REF.Enable()
		_00E_MC_Calia_Purge_REF.Disable()
		InjuredCompanion.ForceRefTo(_00E_MC_Jespar_Purge_REF)
	Else
		MQ17_SC09_CapsuleActivatorREF_Jespar.Enable()
		_00E_MC_Calia_Purge_REF.Enable()
		_00E_MC_Jespar_Purge_REF.Disable()
		InjuredCompanion.ForceRefTo(_00E_MC_Calia_Purge_REF)
	EndIf
	
	If MQ13b_Capsule_Chronikum_REF.IsDisabled()
		MQ13b_Capsule_Chronikum_REF.Enable()
	EndIf
	
	SuntempleWeatherControlTGBXREF.Disable()
	MQ12b_SC14_HarborGuardREF.Disable()
	MQ17_SC10_ChronikumPurge.Enable()
	MQ17_SC09_PurgeLightREF.Enable()
	MQ14_SC01_SuntempleDoorREF.SetOpen(True)
	MQ14_SC01_SuntempleDoorREF.BlockActivation(True)
	MQ15_SC02_EldritchBarrierREF.Disable()
	MQ17_SC09_Glow.Disable()
	Timescale.SetValue(0.001)
	_00E_TimeControl.SkipTimeToHour(13.0)
	MQ17_SC09_PurgerGlimpseMarker.Enable()
	MQ17_ForbiddenRoom_DeadKeeperREF.BlockActivation(True)
	MQ17_ForbiddenRoom_DeadKeeperREF.SetHeadTracking(False)
	MQ17_Temple_Destruction_marker.Enable()
	MQ12b_SC14_SiegeTempleMarker.Disable()
	MQ05Prologue_EmporiumKeeper.Disable()
	_00E_MQ17_Purge_Weather.ForceActive(True)
	MQ17_SC09_CollisionMarker.Enable()
	MQ17_SC09_PlayerInTemple.ForceStart()
	FadeToBlackBackIMOD.ApplyCrossFade(afFadeDuration = 1.0)
	_00E_TeleportGlobal.SetValueInt(0)
	akCompanion.Enable()
	
	if PlayerREF.GetItemCount(_01E_TeleportrolleSonnentempel) == 0 
		PlayerREF.AddItem(_01E_TeleportrolleSonnentempel)
	EndIf
	
	If bHasChosenEndingKatharsis
		Chronicum_Door.BlockActivation(True)
		MQ18b.SetCurrentStageID(5)
		if akCompanion == _00E_MC_CaliaREF
			MQ18b.SetObjectiveDisplayed(7)
		else
			MQ18b.SetObjectiveDisplayed(6)
		endif
	Else
		MQ18a.SetCurrentStageID(5)
		if akCompanion == _00E_MC_CaliaREF
			MQ18a.SetObjectiveDisplayed(7)
		else
			MQ18a.SetObjectiveDisplayed(6)
		endif
	EndIf
	
	MQ17_SC09_Capsule_01_REF.SetName("")
	MQ13b_Capsule_Chronikum_REF.SetName("")
	
	Game.SetPlayerAIDriven(False)
	Game.EnablePlayerControls()
	
EndFunction

Function CompleteObjective()

	If bHasChosenEndingKatharsis
		if akCompanion == _00E_MC_CaliaREF
			MQ18b.SetObjectiveCompleted(7)
		else
			MQ18b.SetObjectiveCompleted(6)
		endif
	Else
		if akCompanion == _00E_MC_CaliaREF
			MQ18a.SetObjectiveCompleted(7)
		else
			MQ18a.SetObjectiveCompleted(6)
		endif
	EndIf

EndFunction

Function FadeBlack()

	Game.ForceFirstPerson()

EndFunction

Function GetIntoTemple()

	Wait(2)
	FadeToBlackBackImod.ApplyCrossFade(afFadeDuration = 3)
	iCleansingLoopSound = _00E_HorrorPulse01Far.Play(PlayerREF)
	_00E_Music_Special_Romance.Remove()
	_00E_SilenceAbruptHighPriority.Remove()
	_00E_PlayerFunctions.GetSoundControl().RemoveSilence()
	_00E_PlayerFunctions.GetSoundControl().RemoveCombatSoundtracks()
	_00E_Music_Special_Cleansing.Add()

EndFunction

Function BlockAllDoors()

	int iIndex = MQ17_SC09_DoorsFRMLST.GetSize() - 1
	
	while iIndex >= 0
		ObjectReference objDoorToBlock = MQ17_SC09_DoorsFRMLST.GetAt(iIndex) as ObjectReference
		objDoorToBlock.BlockActivation(True)
		iIndex -= 1
	endwhile

EndFunction

Function DisableAllNPCs()

	if akCompanion == _00E_MC_CaliaREF
		DiscardedCompanion.ForceRefTo(_00E_MC_JesparREF)
		_00E_MC_JesparREF.MoveTo(_00E_NPCDumpMarker)
	Else
		DiscardedCompanion.ForceRefTo(_00E_MC_CaliaREF)
		_00E_MC_CaliaREF.MoveTo(_00E_NPCDumpMarker)
	EndIf
	
	MQ14_SC06_TraitorRef.Disable()
	MQ12b_SC3_CityGuardREF.Disable()
	DisableIfEnabled(_00E_MC_LeoraREF)
	DisableIfEnabled(_00E_MC_TealorREF)
	DisableIfEnabled(_00E_MC_LexREF)
	DisableIfEnabled(_00E_MC_YuslanRef)
	DisableIfEnabled(_00E_MC_LishariREF)
	DisableIfEnabled(_00E_MC_NataraREF)
	DisableIfEnabled(SuntempleGuardREFBasement)
	DisableIfEnabled(_00E_MC_KonstantinREF)
	DisableIfEnabled(_00E_MC_JorrekRef)
	DisableIfEnabled(_00E_MC_YaelaREF)
	DisableIfEnabled(Suntemple_HighPriestAkawiaREF)
	DisableIfEnabled(MQ16_StubbornGuardREF)

EndFunction

Function DisableIfEnabled(Actor akNPC)

	if akNPC.IsEnabled()
		akNPC.Disable()
	EndIf

EndFunction

Function SetUnconsciousCompanion()

	InjuredCompanion.GetActorReference().SetUnconscious(True)
	InjuredCompanion.GetActorReference().SetHeadTracking(False)
	InjuredCompanion.GetActorReference().SetLookAt(MQ17_SC09_CompanionLook)
	InjuredCompanion.GetActorReference().BlockActivation(True)
	
	if akCompanion == _00E_MC_CaliaREF
		MQ17_SC09_JesparBody.Reset()
		MQ17_SC09_JesparBody.SetPosition(-4400, -2197, -9383)
		MQ17_SC09_JesparBody.Enable()
	Else
		MQ17_SC09_CaliaBody.Reset()
		MQ17_SC09_CaliaBody.SetPosition(-4400, -2197, -9383)
		MQ17_SC09_CaliaBody.Enable()
	EndIf
	
	
EndFunction

Function SetUnconsciousTealor()

	MQ17_SC09_TealorPurgeREF.SetUnconscious(True)
	MQ17_SC09_TealorPurgeREF.SetHeadTracking(False)
	
EndFunction

Function GetCompanionForCapsule()

	_00E_Music_Special_Cleansing.Remove()
	_00E_SilenceAbruptHighPriority.Add()
	MQ13b_Capsule_Chronikum_REF.SetOpen(True)
	MQ18a.SetObjectiveCompleted(5)
	Game.DisablePlayerControls()
	FadeToBlackImod.Apply()
	Wait(2)
	FadeToBlackHoldIMOD.ApplyCrossFade(afFadeDuration = 1.0)
	MQ17_SC10_LaunchActivatorREF.Enable()
	MQ17_SC09_CompanionChairMarker.Enable()
	
	If akCompanion.IsDisabled()
		akCompanion.Enable()
	EndIf
	
	PlayerREF.MoveTo(MQ17_SC10_PlayerPrepareCapsuleMarker)
	akCompanion.MoveTo(MQ17_SC09_CompanionChairMarker)
	_00E_Purge_ShaderFX.Play(akCompanion)
	
	If MQ17_SC09_CapsuleActivatorREF_Calia.IsEnabled()
		MQ17_SC09_CapsuleActivatorREF_Calia.Disable()
	EndIf
	
	If MQ17_SC09_CapsuleActivatorREF_Jespar.IsEnabled()
		MQ17_SC09_CapsuleActivatorREF_Jespar.Disable()
	EndIf
	
	MQ18a.SetObjectiveDisplayed(10)
	
	MQ17_SC10_LaunchSequence.ForceStart()
	
EndFunction

Function FadeBack()

	FadeToBlackImod.Remove()
	FadeToBlackBackIMOD.ApplyCrossFade(afFadeDuration = 1.0)
	MQ17_SC09_Capsule_01_REF.SetName("Sternlingskapsel")
		
EndFunction

Function CloseCompanionCapsule()

	MQ13b_Capsule_Chronikum_REF.SetOpen(False)
	_00E_Capsule_Close_SDM.Play(PlayerREF)
	MQ13b_Capsule_Chronikum_REF.BlockActivation(True)
	Utility.Wait(2)
	Game.EnablePlayerControls()
	
EndFunction

Function PlayerResurrectFailsave()

	; This fires if the player AI has somehow failed to "seat" him into the capsule. Check MQ17_SC10, Phase 4 for reference.
	
	PlayerREF.Resurrect()

EndFunction

Function LaunchCapsule()

	Game.DisablePlayerControls(True, True, True, True, True, True)
	Wait(1)
	MQ17_SC09_Capsule_01_REF.SetOpen(False)
	_00E_Capsule_Close_SDM.Play(PlayerREF)
	Wait(3)
	MQ17_SC10_CapsuleLaunchStonesREF.Enable()
	int iCapsuleLaunch = _00E_Capsule_LaunchM.Play(PlayerREF)
	Sound.SetInstanceVolume(iCapsuleLaunch, 0.3)
	Wait(11.5)
	_00E_MQ17_SC10_AccelerateIMOD.Apply()
	FXExplosionFirestormNearM.Play(PlayerREF)
	PlayerREF.TranslateTo(PlayerREF.GetPositionX(), PlayerREF.GetPositionY(), (PlayerREF.GetPositionZ() + 9000.0), PlayerREF.GetAngleX(), PlayerREF.GetAngleY(), PlayerREF.GetAngleZ(), 700.0, 700.0)
	MQ17_SC09_Capsule_01_REF.TranslateTo(MQ17_SC09_Capsule_01_REF.GetPositionX(), MQ17_SC09_Capsule_01_REF.GetPositionY(), (MQ17_SC09_Capsule_01_REF.GetPositionZ() + 9000.0), MQ17_SC09_Capsule_01_REF.GetAngleX(), MQ17_SC09_Capsule_01_REF.GetAngleY(), MQ17_SC09_Capsule_01_REF.GetAngleZ(), 710.0, 710.0)
	Game.ShakeCamera(afStrength = 0.5, afDuration = 0.5)
	Wait(0.5)
	FXExplosionCatapultNearM.Play(PlayerREF)
	Game.ShakeCamera(afStrength = 1.0, afDuration = 7)
	MQ17_SC10_CapsuleLaunchStonesREF.PlaceAtMe(FXdustDropMedExplosion)
	MQ17_SC10_CapsuleLaunchStonesREF.PlayAnimation("PlayAnim02")
	MQ17_SC10_CeilingIntact.DisableNoWait()
	MQ17_SC10_CeilingICollapsed.EnableNoWait()
	Sound.StopInstance(iCleansingLoopSound)
	Wait(7)
	FadeToWhiteHoldImod.ApplyCrossFade(afFadeDuration = 1.0)
	Wait(3)
	PlayerREF.StopTranslation()
	MQ17_SC09_Capsule_01_REF.StopTranslation()
	SetCurrentStageID(150)
	
EndFunction

Function DestroyBlackStone(ObjectReference akStoneToDestroy)

	if akStoneToDestroy.IsEnabled()

		akStoneToDestroy.PlaceAtMe(_00E_MQ17_BlackStoneExplosion)
		akStoneToDestroy.PlaceAtMe(ExplosionRuneShock02)
		akStoneToDestroy.GetLinkedRef().DisableNoWait(True)
		akStoneToDestroy.Disable()
		_00E_MQ16_EchoScreamsM.Play(PlayerREF)
		Game.ShakeCamera(afStrength = 0.1)
		iBlackStonesDestroyed ==  iBlackStonesDestroyed + 1
		
		If MQ12a_SC1_BlackStone01.IsDisabled() && MQ12a_SC3_BlackStone03.IsDisabled() && MQ12a_SC1_BlackStone02.IsDisabled()
			DestroyBeacon()
		EndIf
	
		Return
		
	EndIf
	
EndFunction

Function DestroyBeacon()

	MQ18b.SetObjectiveCompleted(5)
	_00E_Music_Special_Cleansing.Remove()
	_00E_SilenceAbruptHighPriority.Add()
	SetCurrentStageID(130)
	QSTDwemerGong01.Play(PlayerREF)
	Game.ShakeCamera(afStrength = 0.1, afDuration = 3.0)
	FadeToWhiteImod.Apply()
	Wait(1)
	FadeToWhiteHoldImod.ApplyCrossFade(afFadeDuration = 1.0)
	Wait(9.5)
	SetCurrentStageID(150)
	
EndFunction

Function SetUpEpilogue()

	if bHasChosenEndingKatharsis
	
		if _00E_FS_DreamflowerConsumed.GetValueInt() == 1
		
			FS_MQ18c.SetCurrentStageID(5)
		
		Else
	
			MQ18b.SetCurrentStageID(10)
			MQ18b.SetUpDreamScene(True)
			
		EndIf
		
	Else
		MQ18b.SetUpDreamScene(False)
		MQ18a.SetCurrentStageID(10)
	EndIf
		
	Self.CompleteQuest()
	
EndFunction

Function AddRomanceMusic()
	
	If _00E_Music_Special_Romance == None
		_00E_Music_Special_Romance = Game.GetForm(0x0013FA93) as MusicType
	EndIf

	_00E_Music_Special_Romance.Add()

EndFunction

;=====================================================================================
;              							PROPERTIES                    					 
;=====================================================================================

int iPortalSound
int iVisionCount
int iVisionIntenseSound
int iHeartActiveSound
int iHeartActiveSound02
int Property iCleansingLoopSound Auto Hidden
int iBlackStonesDestroyed 

Formlist emptyFormlist

bool Property bIsVisionPlaying Auto Conditional Hidden
bool Property bIsCaliaCompanion Auto Conditional Hidden
bool Property bHasChosenEndingKatharsis Auto Conditional Hidden
bool Property bTalkedToTealor Auto Conditional Hidden

ReferenceAlias Property Companion Auto
ReferenceAlias Property InjuredCompanion Auto
ReferenceAlias Property DiscardedCompanion Auto

Topic Property MQ17_D04_FinalFightScream Auto
Topic Property MQ17_D01_VisionBranchTopic Auto

Actor Property akCompanion Auto Hidden

Armor Property _00E_InvisibleHelmet_Armor Auto

_00E_MQ16_Functions Property MQ16 Auto
_00E_MQ18b_Functions Property MQ18b Auto
_00E_MQ18a_Functions Property MQ18a Auto

Quest Property FS_MQ18c Auto

SoundCategory Property AudioCategorySFX Auto
SoundCategory Property AudioCategoryMAG Auto

Weather Property _00E_MQ17_Purge_Weather Auto

GlobalVariable Property JesparNoCombatComments Auto

Ammo Property _00E_MQ11a_SC12_FireArrows Auto

Scroll Property _01E_TeleportrolleSonnentempel Auto

Actor Property _00E_MC_VeiledWomanREF Auto
Actor Property PlayerREF Auto
Actor Property _00E_MC_CaliaREF Auto
Actor Property _00E_MC_JesparREF Auto
Actor Property MQ17_SC06_CameraREF Auto
Actor Property _00E_MC_LeoraREF Auto
Actor Property _00E_MC_TealorREF Auto
Actor Property _00E_MC_LexREF Auto
Actor Property _00E_MC_YuslanRef Auto
Actor Property _00E_MC_LishariREF Auto
Actor Property _00E_MC_KonstantinREF Auto
Actor Property _00E_MC_NataraREF Auto
Actor Property _00E_MC_JorrekRef Auto
Actor Property _00E_MC_YaelaREF Auto
Actor Property _00E_MC_Calia_Purge_REF Auto
Actor Property _00E_MC_Jespar_Purge_REF Auto
Actor Property MQ17_SC09_TealorPurgeREF Auto
Actor Property Suntemple_HighPriestAkawiaREF Auto
Actor Property MQ16_StubbornGuardREF Auto
Actor Property SuntempleGuardREFBasement Auto 
Actor Property MQ17_ForbiddenRoom_DeadKeeperREF Auto 
Actor Property MQ17_Generator_Left_REF003 Auto
Actor Property MQ17_Generator_Right_REF003 Auto

ObjectReference Property MQ17_SC07_BlackGuardianVoice Auto

Activator Property _00E_MQ17_BlackGuardianJaw Auto

_00E_VisionFX_NPC_SC Property MQ17_SC02_PyreanChroniclerREF Auto
_00E_VisionFX_NPC_SC Property MQ17_SC02_PyreanOfficerREF Auto

_00E_TestBossFightSC Property MQ17_CombatControllerREF Auto

Idle Property TG05_Knockout Auto
Idle Property TG05_GetUp Auto
Idle Property WebIdleExit Auto
Idle Property pa_Idle_Kiss_MaleMale Auto
Idle Property pa_Idle_Kiss_MaleFemale Auto
Idle Property pa_Idle_Kiss_FemaleMale Auto
Idle Property pa_Idle_Kiss_FemaleFemale Auto

VisualEffect Property AbsorbCastVFX01 Auto
VisualEffect Property AbsorbTargetVFX01Orange Auto

Spell Property _00E_MQ17_SC06_FlamingArrowSP Auto
Spell Property _00E_Game_abSlowTime Auto

EffectShader Property _00E_Purge_ShaderFX Auto

GlobalVariable Property _00E_TeleportGlobal Auto
GlobalVariable Property Timescale Auto
GlobalVariable Property MQ17_JesparFinalCompanion Auto
GlobalVariable Property CompanionIsTalking Auto
GlobalVariable Property MQ17_BlackGuardianIsTalking Auto
GlobalVariable Property _00E_FS_DreamflowerConsumed Auto
GlobalVariable Property _00E_VideoSkip Auto

ImageSpaceModifier Property _00E_MQ16_VisionIMOD Auto
ImageSpaceModifier Property _00E_MQ17_SC06_TransformConsciousnessIMOD Auto
ImageSpaceModifier Property FadeToBlackHoldIMOD Auto
ImageSpaceModifier Property _00E_MQ17_SC01_VeiledWomanFade Auto
ImageSpaceModifier Property _00E_MQ17_SC01_PlayerAwakeIMOD Auto
ImageSpaceModifier Property _00E_MQ17_SC06_FireArrowImpactIMOD Auto
ImageSpaceModifier Property MAGFireExpertHitImod Auto
ImageSpaceModifier Property MAGShockExpImod Auto
ImageSpaceModifier Property _00E_MQ17_SC08_BlackGuardianCollapseIMOD Auto
ImageSpaceModifier Property alduinExplosionFlashImod Auto
ImageSpaceModifier Property FadeToBlackImod Auto
ImageSpaceModifier Property FadeToBlackBackImod Auto
ImageSpaceModifier Property FadeToWhiteImod Auto
ImageSpaceModifier Property FadeToWhiteHoldImod Auto
ImageSpaceModifier Property _00E_MQ17_SC10_AccelerateIMOD Auto
ImageSpaceModifier Property FadeToBlackAndBackIMOD Auto

ObjectReference Property MQ17_SC01_PlayerWakeUpMarker Auto
ObjectReference Property MQ17_SC01_PlayerWakeUpMarkerFailsave Auto
ObjectReference Property MQ17_SC01_VeiledWomanStartMarker Auto
ObjectReference Property MQ17_SC01_VeiledWomanStartMarkerFailsave Auto
ObjectReference Property MQ17_SC01_PortalDoorFailsave Auto
ObjectReference Property MQ17_SC01_RailREF Auto
ObjectReference Property MQ17_SC02_PlayerStart Auto

ObjectReference Property MQ17_SC02_BlackGuardianLightLinker Auto
ObjectReference Property MQ17_SC05_BlackGuardianButton Auto
ObjectReference Property MQ17_SC06_BlackGuardianHeartREF Auto
ObjectReference Property MQ17_SC06_AbsorbLightREF Auto
ObjectReference Property MQ17_SC06_CompanionSpawnMarker Auto
ObjectReference Property MQ17_SC06_PillarREF Auto
ObjectReference Property MQ17_SC06_AbsorbLightREFPlayer Auto
ObjectReference Property MQ17_SC06_CameraPos Auto
ObjectReference Property MQ17_SC06_PillarExitMarker Auto
ObjectReference Property MQ16_SC07_FightLinker Auto
ObjectReference Property MQ17_SC07_Fire_002 Auto
ObjectReference Property MQ17_SC07_Fire_001 Auto
ObjectReference Property MQ17_SC08_Death_Right_001 Auto
ObjectReference Property MQ17_SC08_Death_Right_002 Auto
ObjectReference Property MQ17_SC08_Death_Right_003 Auto
ObjectReference Property MQ17_SC08_Death_Right_004 Auto
ObjectReference Property MQ17_SC08_Death_Left_001 Auto
ObjectReference Property MQ17_SC08_Death_Left_002 Auto
ObjectReference Property MQ17_SC08_Death_Left_003 Auto
ObjectReference Property MQ17_SC08_Death_Left_004 Auto
ObjectReference Property MQ17_SC08_Death_Chest Auto
ObjectReference Property MQ17_SC07_BlackGuardianJaw_REF002 Auto
ObjectReference Property MQ17_SC07_FireFXREF003 Auto
ObjectReference Property MQ17_SC08_DeathSmoke Auto
ObjectReference Property MQ17_SC07_MouthLightREF001 Auto
ObjectReference Property MQ16_SC10_VisionActorREF Auto
ObjectReference Property MQ17_SC07_BlackGuardianJaw_Cast001 Auto
ObjectReference Property MQ17_SC08_SoundMarker Auto
ObjectReference Property MQ17_SC08_LightRefREF Auto
ObjectReference Property MQ17_SC08_PlayerMarker01 Auto
ObjectReference Property MQ17_SC08_CompanionMarker Auto
ObjectReference Property MQ17_SC09_CollisionMarker Auto
ObjectReference Property MQ17_SC09_PurgerGlimpseMarker Auto
ObjectReference Property MQ15_SC02_EldritchBarrierREF Auto
ObjectReference Property MQ14_SC01_SuntempleDoorREF Auto
ObjectReference Property MQ17_SC06_FalmerKeys Auto
ObjectReference Property MQ17_Temple_Destruction_marker Auto
ObjectReference Property LeuchtfeuerSwitcher Auto
ObjectReference Property MQ14_SC04_BarrierREF Auto
ObjectReference Property MQ12b_SC14_SiegeTempleMarker Auto
ObjectReference Property MQ17_SC09_CompanionLook Auto
ObjectReference Property MQ17_SC09_CaliaBody Auto
ObjectReference Property MQ17_SC09_JesparBody Auto
ObjectReference Property MQ17_SC09_PurgeLightREF Auto
ObjectReference Property MQ17_SC09_Glow Auto
ObjectReference Property MQ17_SC09_Capsule_01_REF Auto
ObjectReference Property MQ13b_Capsule_Chronikum_REF Auto
ObjectReference Property MQ17_SC09_CapsuleActivatorREF_Calia Auto
ObjectReference Property MQ17_SC09_CapsuleActivatorREF_Jespar Auto
ObjectReference Property MQ17_SC09_CompanionChairMarker Auto
ObjectReference Property MQ17_SC10_LaunchActivatorREF Auto
ObjectReference Property MQ17_SC10_ChronikumPurge Auto
ObjectReference Property MQ17_SC10_PlayerPrepareCapsuleMarker Auto
ObjectReference Property MQ17_SC10_CapsuleLaunchStonesREF Auto
ObjectReference Property MQ06_CaliaPointChronikumMarkerDUPLICATE001 Auto
ObjectReference Property MQ17_SC10_CeilingIntact Auto
ObjectReference Property MQ17_SC10_CeilingICollapsed Auto
ObjectReference Property MQ12a_SC3_BlackStone03 Auto
ObjectReference Property SuntempleWeatherControlTGBXREF Auto
ObjectReference Property MQ12a_SC1_BlackStone02 Auto
ObjectReference Property MQ12a_SC1_BlackStone01 Auto
ObjectReference Property MQ14_SC04_SmokeREF Auto
ObjectReference Property Chronicum_Door Auto
ObjectReference Property MQ12b_SC14_HarborGuardREF Auto
ObjectReference Property MQ05Prologue_EmporiumKeeper Auto
ObjectReference Property MQ17_EntranceDoorREF Auto
ObjectReference Property _00E_NPCDumpMarker Auto
ObjectReference Property MQ14_SC06_TraitorRef Auto
ObjectReference Property MQ12b_SC3_CityGuardREF Auto

Weapon Property _02E_11Eichenbogen Auto

Explosion Property ExplosionRuneShock02 Auto
Explosion Property _00E_FXDustExplosionSmaller Auto
Explosion Property _00E_A2_StarlingdummyDetExp Auto
Explosion Property DA16SkullAreaExplosion Auto
Explosion Property _00E_FireballExpSmallHarmless Auto
Explosion Property _00E_HarmlessFireExplosion Auto
Explosion Property FXdustDropMedExplosion Auto
Explosion Property _00E_MQ17_BlackStoneExplosion Auto

EffectShader Property TimeFadeIn01FXS Auto
EffectShader Property TimeFadeOut01FXS Auto

Formlist Property MQ17_SC09_DoorsFRMLST Auto
Formlist Property MQ17_KeepersToDisable Auto

Scene Property MQ17_SC01_PlayerWakesUpSC Auto
Scene Property MQ17_SC02_Vision_01_SC Auto
Scene Property MQ17_SC02_Vision_02_SC Auto
Scene Property MQ17_SC02_Vision_03_SC Auto
Scene Property MQ17_SC03_BlackGuardian_01 Auto
Scene Property MQ17_SC04_BlackGuardian_02 Auto
Scene Property MQ17_SC05_BlackGuardian_03 Auto
Scene Property MQ17_SC06_BlackGuardianTriesToTrapPlayer Auto
Scene Property MQ17_SC07_BlackGuardianFight Auto
Scene Property MQ17_SC08_PreCleansing Auto
Scene Property MQ17_SC09_PlayerInTemple Auto
Scene Property MQ17_SC10_LaunchSequence Auto

Formlist Property MQ17_SC02_VisionsInvolvedList Auto

MusicType Property _00E_Music_Combat_Epic Auto
MusicType Property _00E_Music_Special_Cleansing Auto
MusicType Property _00E_SilenceAbruptHighPriority Auto
MusicType Property _00E_Music_Special_Zyklus_OneSelection Auto
MusicType Property _00E_Music_Special_Romance Auto
MusicType Property _00E_Music_Special_MQ17_BlackGuardian Auto

Sound Property QSTSovengardePortalOn2DLPM Auto
Sound Property _00E_A2_Ghostwalk_TeleportDoneSound Auto
Sound Property MAGRestorationFFFire Auto
Sound Property _00E_AltIshmartepElectroShotSound Auto
Sound Property QSTDA10Rumble Auto
Sound Property QSTDA02ShrineActivateLPMM Auto
Sound Property QSTUstengravRumble2DLPM Auto
Sound Property _00E_MAGFXFireOilIgniteLow Auto
Sound Property NPCDwarvenCenturionDeathM Auto
Sound Property FXExplosionFirestormNearM Auto
Sound Property TRPDwemerPistonOutM Auto
Sound Property _00E_MQ13c_TurretChargeSoundM Auto
Sound Property FXExplosionCatapultNearM Auto
Sound Property MAGShockFFFireM Auto
Sound Property _00E_HorrorPulse01Far Auto
Sound Property _00E_Capsule_LaunchM Auto
Sound Property _00E_Capsule_Close_SDM Auto
Sound Property QSTDwemerGong01 Auto
Sound Property QSTAlduinDeathExplosionA Auto
Sound Property _00E_HorrorPulseFarSingleM Auto
Sound Property _00E_MQ17_BlackGuardianScreamsM Auto
Sound Property _00E_MQ16_EchoScreamsM Auto
