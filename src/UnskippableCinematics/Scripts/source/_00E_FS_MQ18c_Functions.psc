Scriptname _00E_FS_MQ18c_Functions extends Quest  

int function _GetScriptVersion() Global
    return 1
endFunction

;=====================================================================================
;              							FUNCTIONS                    					 
;=====================================================================================

Function SetUpDreamScene()

	AllowIdleChatter.SetValue(0)
	Game.ForceFirstPerson()
	Game.ShowFirstPersonGeometry(False)
	_00E_SilenceAbruptHighPriority.Add()
	Weather.ReleaseOverride()
	FS_MQ18c_TriggerboxREF.Enable()
	FS_MQ18c_TreeLinker.Disable()
	
	If MQ17_JesparFinalCompanion.GetValue() == 1
		FS_MQ18c_JesparNewREF.SetOutfit(_00E_FS_MQ18c_JesparOutfits)
		akCompanion = FS_MQ18c_JesparNewREF
	Else
		FS_MQ18c_CaliaNewREF.SetOutfit(_00E_CQC06_CaliaDanceOutfit)
		akCompanion = FS_MQ18c_CaliaNewREF
	EndIf
	
	akCompanion.RemoveAllItems()
	Companion.ForceRefTo(akCompanion)

	PlayerREF.MoveTo(PlayerStartMarkerNew)
	SkyrimStormRain.ForceActive(True)

	_00E_Func_ReferenceFormList.Disable(FS_MQ18c_StuffToDisable)

	; if Player.GetSex() == 1
		; FS_MQ18c_PlayerREF.Disable()
		; FS_MQ18c_PlayerFemaleREF.Enable()
		; akPlayerCorpse = FS_MQ18c_PlayerFemaleREF
		
	; elseif Player.GetSex() == 0
		FS_MQ18c_PlayerFemaleREF.Disable()
		FS_MQ18c_PlayerREF.Enable()
		akPlayerCorpse = FS_MQ18c_PlayerREF
	; endif
	
	Corpse.ForceRefTo(akPlayerCorpse)
	akPlayerCorpse.MoveTo(FS_MQ18c_CradleFurnMarkerREF)
	FS_MQ18c_ParentREF.Enable()
	
	MQ18_Linker.Disable()
	;they need to be disabled manually because of their usage in other quests
	MQ10a_SC1_FireREF_01.Disable()
	MQ10a_SC1_FireREF_02.Disable()
	MQ10a_SC1_FireREF_03.Disable()
	MQ10a_SC1_FireREF_04.Disable()
	
	FS_MQ18c_ActivatorREF.Enable()
	MQP01_DreamDoorREF.BlockActivation(False)
	MQP01_DreamDoorREF.SetOpen(False)
	MQ10a_SC1_MotherREF.Disable()
	PlayerREF.UnequipAll()
	MQ10a_SC1_SisterREF.Disable()
	MQP01_FatherRef.Disable()
	MQ10a_SC1_FatherREF.Disable()
	MQ12c_SC03_FatherREF.Disable()
	MQ18b_HouesLight.Disable()
	Timescale.SetValue(0.1)
	_00E_TimeControl.SkipTimeToHour(0.0)
	
	Utility.Wait(2)
	FadeToWhiteBackIMOD.ApplyCrossFade(afFadeDuration = 3.0)
	Game.SetPlayerAIDriven(False)
	Game.EnablePlayerControls()
	Game.DisablePlayerControls(false, true, true, false, true, false, false)
	FS_MQ18c_SC00_CorpseSC.ForceStart()

EndFunction

Function PreparePlayer()

	FS_MQ18c_ActivatorREF.Disable()
	Game.DisablePlayerControls()
	_00E_FS_MQ18c_SweetDreamsType.Add()
	Utility.Wait(8)
	_00E_FS_MQ18c_DissolveCorpse.Play(akPlayerCorpse)
	_00E_FS_MQ18c_FakeFadeToBlackIMOD.Apply()
	Utility.Wait(12.0)
	Awaken()
	
EndFunction

Function PrepareBody()

	akPlayerCorpse.RemoveSpell(AbDraugr)
	akPlayerCorpse.MoveTo(FS_MQ18c_CradleFurnMarkerREF)
	FS_MQ18c_StartAnim.SetValueInt(1)
	akPlayerCorpse.EvaluatePackage()
	akPlayerCorpse.EnableAI(False)
	
EndFunction

Function Awaken()

	Game.ShakeCamera(afStrength = 1.0)
	_00E_FS_MQ18c_DissolveCorpse.Stop(akPlayerCorpse)
	_00E_FS_NQR05_TharaelMaterializeFXS.Play(akPlayerCorpse)
	akPlayerCorpse.EnableAI(True)
	FS_MQ18c_StartAnim.SetValueInt(1)
	akPlayerCorpse.SetRestrained(True)
	akPlayerCorpse.EvaluatePackage()
	FS_MQ18c_AwakenLightREF.Enable()
	MAGFireBallExpImod.ApplyCrossFade(afFadeDuration = 0.1)
	_00E_FS_MQ18c_FakeFadeToBlackIMOD.Remove()
	FireFXShader.Play(akPlayerCorpse)
	Game.ShakeCamera(afStrength = 0.3, afDuration = 7.0)
	MAGDestructionFireballExplosionM.Play(PlayerREF)
	FS_MQ18c_FireREF01.EnableNoWait()
	_00E_FS_MQ18c_SweetDreamsScreamsM.Play(akPlayerCorpse)
	Utility.Wait(6.75)
	FadeToBlackHoldImod.Apply()
	Utility.Wait(5.0)
	SetUpQyraScene()
	
EndFunction

Function SetUpQyraScene()

	Game.ForceThirdPerson()
	PlayerREF.MoveTo(FS_MQ18c_SC01_BedMarkerREF)
	_00E_PlayerFunctions.GetSafeItemRemove().RemoveAllItemsSafeVersion(None)
	PlayerREF.AddItem(_00E_EndreleanSublimeGarb_Blue, 1, true)
	
	if SKSE.GetVersion()
		PlayerREF.EquipItemEx(_00E_EndreleanSublimeGarb_Blue, 0, true)
	else
		PlayerREF.equipitem(_00E_EndreleanSublimeGarb_Blue, true, true)
	endif
	
	Game.SetPlayerAIDriven(True)
	Game.DisablePlayerControls()
	Weather.ReleaseOverride()
	AllowIdleChatter.SetValue(0)
	Companion.GetReference().Enable()
	Companion.GetReference().MoveTo(FS_MQ18c_CompanionSitMarkerREF)
	Timescale.SetValue(0.01)
	_00E_TimeControl.SkipTimeToHour(18.75)
	FS_MQ18c_SC01_QyraSC.ForceStart()
	SkyrimClear.ForceActive(True)
	_00E_BloodyFXShader.Stop(PlayerREF)
	
EndFunction
 
Function FadeBack()

	_00E_Music_Special_Dreams.Remove()
	Game.ForceThirdPerson()
	Game.SetPlayerAIDriven(False)
	FS_MQ18c_SC01_BedMarkerREF.Activate(PlayerREF)
	String facegen = "bUseFaceGenPreprocessedHeads:General"
	Utility.SetINIBool(facegen, False)
	Game.GetPlayer().QueueNiNodeUpdate()
	Utility.SetINIBool(facegen, True)
	FadeToBlackHoldIMOD.Remove()
	FadeToBlackBackLongImod.ApplyCrossFade()

	if	MQ17_JesparFinalCompanion.GetValue() == 1
		SetObjectiveDisplayed(5)
	Else
		SetObjectiveDisplayed(10)
	EndIf

	Utility.wait(0.1)
	Game.EnablePlayerControls()
	FS_MQ18c_SC01_BedMarkerREF.BlockActivation(true)
	SetCurrentStageID(16)
	
EndFunction

Function AddSilence()

	_00E_SilenceLongTransitionHighPriority.Add()

EndFunction

Function AddMusic()

	_00E_SilenceLongTransitionHighPriority.Remove()
	_00E_FS_Music_Special_DreamflowerEndingType.Add()

EndFunction

Function ShowCredits()

	Debug.ToggleMenus()
	Steam.UnlockAchievement("END_COMPLETE_MQ18C_01")
	FadeToBlackHoldIMOD.Apply()
	Utility.Wait(8)
	; ZP: not interruptible - a key press ended it at once
	Game.PlayBink("Enderal_Credits.bik", false)
	FadeToBlackHoldIMOD.Remove()
	Debug.ToggleMenus()
	_00E_Game_PostCreditsMessage.Show()
	Game.QuitToMainMenu()

EndFunction

;=====================================================================================
;              							PROPERTIES                    					 
;=====================================================================================

int iWindSound

GlobalVariable Property AllowIdleChatter Auto

Actor akPlayerCorpse

Actor Property akCompanion Auto Hidden

ActorBase Property Player Auto

Armor Property _00E_EndreleanSublimeGarb_Blue Auto

Actor Property PlayerREF Auto
Actor Property MQP01_FatherRef Auto
Actor Property MQ10a_SC1_FatherREF Auto
Actor Property MQ10a_SC1_SisterREF Auto
Actor Property MQ10a_SC1_MotherREF Auto
Actor Property MQ12c_SC03_FatherREF Auto
Actor Property FS_MQ18c_JesparNewREF Auto
Actor Property FS_MQ18c_CaliaNewREF Auto
Actor Property FS_MQ18c_PlayerREF Auto
Actor Property FS_MQ18c_PlayerFemaleREF Auto

Weather Property SkyrimStormRain Auto
Weather Property SkyrimClear Auto

Formlist Property FS_MQ18c_StuffToDisable Auto

MusicType Property _00E_SilenceAbruptHighPriority Auto
MusicType Property _00E_FS_MQ18c_SweetDreamsType Auto
MusicType Property _00E_Music_Special_Dreams Auto
MusicType Property _00E_FS_Music_Special_DreamflowerEndingType Auto
MusicType Property _00E_SilenceLongTransitionHighPriority Auto

EffectShader Property _00E_FS_MQ18c_DissolveCorpse Auto
EffectShader Property _00E_FS_NQR05_TharaelMaterializeFXS Auto
EffectShader Property _00E_BloodyFXShader Auto

Sound Property _00E_MAGFXFireOilIgniteLow Auto
Sound Property _00E_FS_MQ18c_SweetDreamsScreamsM Auto
Sound Property MAGDestructionFireballExplosionM Auto
Sound Property AMBWindloopMountainsCLP Auto

ReferenceAlias Property Corpse Auto
ReferenceAlias Property Companion Auto

ImageSpaceModifier Property FadeToWhiteBackIMOD Auto
ImageSpaceModifier Property MAGFireBallExpImod Auto
ImageSpaceModifier Property _00E_MQ11c_DreamCollapseIMOD Auto
ImageSpaceModifier Property FadeToWhiteHoldImod Auto
ImageSpaceModifier Property FadeToBlackHoldIMOD Auto
ImageSpaceModifier Property _00E_FS_MQ18c_FakeFadeToBlackIMOD Auto
ImageSpaceModifier Property FadeToBlackBackLongImod Auto

Idle Property TG05_Knockout Auto
Idle Property TG05_GetUp Auto

Outfit Property _00E_CQC06_CaliaDanceOutfit Auto
Outfit Property _00E_FS_MQ18c_JesparOutfits Auto

EffectShader Property FireFXShader Auto

GlobalVariable Property Timescale Auto
GlobalVariable Property MQ17_JesparFinalCompanion Auto

Scene Property FS_MQ18c_SC01_QyraSC Auto
Scene Property FS_MQ18c_SC00_CorpseSC Auto

Message Property _00E_Game_PostCreditsMessage Auto

ObjectReference Property MQP01_SC02_Elk Auto
ObjectReference Property MQ10a_SC1_FireREF_01 Auto
ObjectReference Property MQ10a_SC1_FireREF_02 Auto
ObjectReference Property MQ10a_SC1_FireREF_03 Auto
ObjectReference Property MQ10a_SC1_FireREF_04 Auto
ObjectReference Property MQ18b_HouesLight Auto
ObjectReference Property MQP01_DreamDoorREF Auto
ObjectReference Property MQ18_Linker Auto
ObjectReference Property PlayerStartMarkerNew Auto
ObjectReference Property FS_MQ18c_SC01_BedMarkerREF Auto
ObjectReference Property FS_MQ18c_ParentREF Auto
ObjectReference Property FS_MQ18c_CradlesRef Auto
ObjectReference Property FS_MQ18c_FireREF01 Auto
ObjectReference Property FS_MQ18c_CradleFurnMarkerREF Auto
ObjectReference Property FS_MQ18c_TriggerboxREF Auto
ObjectReference Property FS_MQ18c_TreeLinker Auto
ObjectReference Property FS_MQ18c_AwakenLightREF Auto
ObjectReference Property FS_MQ18c_RainParentREF Auto
ObjectReference Property FS_MQ18c_MotherREF Auto
ObjectReference Property FS_MQ18c_SisterREF Auto
ObjectReference Property FS_MQ18c_ActivatorREF Auto
ObjectReference Property FS_MQ18c_CompanionSitMarkerREF Auto

Spell Property AbDraugr Auto

GlobalVariable Property FS_MQ18c_StartAnim Auto
