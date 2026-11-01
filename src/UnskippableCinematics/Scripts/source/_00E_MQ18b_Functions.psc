Scriptname _00E_MQ18b_Functions extends Quest  
 
 int function _GetScriptVersion() Global
    return 1
endFunction
 
 ;=====================================================================================
;              							EVENTS                    					 
;=====================================================================================
 
 Event OnUpdate()
 
	Debug.ToggleCollisions()
	PlayerREF.SplineTranslateToREF(MQ18b_FloatAwayMarker, 30.0, 30.0, 30.0)
	_00E_MQ18b_EndingIMOD.Apply()

EndEvent
 
 
;=====================================================================================
;              							FUNCTIONS                    					 
;=====================================================================================

Function AddMusic()

	_00E_SilenceAbruptHighPriority.Remove()
	_00E_Music_Special_MQ18b_Katharsis.Add()

EndFunction

Function FadeOut()

	FadeToWhiteHoldIMOD.ApplyCrossFade(afFadeDuration = 3)
	Utility.Wait(6)
	Debug.ToggleMenus()
	Steam.UnlockAchievement("END_COMPLETE_MQ18B_01")
	Debug.ToggleCollisions()
	; ZP: not interruptible - a key press ended it at once
	Game.PlayBink("Enderal_Credits.bik", false)
	FadeToWhiteHoldIMOD.Remove()
	Debug.ToggleMenus()
	_00E_Game_PostCreditsMessage.Show()
	Game.QuitToMainMenu()

EndFunction

Function SetUpBeacon()

	MQ12a_SC1_BlackStone01.Enable()
	MQ12a_SC1_BlackStone02.Enable()
	MQ12a_SC3_BlackStone03.Enable()

EndFunction

Function SetUpDreamScene(bool bKatharsis)

	_FS_Phasmalist_ControlQuest.UnsummonApparitionIfExists()
	AllowIdleChatter.SetValue(0)
	Game.ForceFirstPerson()
	Game.ShowFirstPersonGeometry(False)
	_00E_SilenceAbruptHighPriority.Add()
	Weather.ReleaseOverride()
	PlayerREF.MoveTo(PlayerStartMarkerNew)
	_00E_MQ18_EpilogueWeather.ForceActive(True)
	MQ18_Linker.Disable()
	MQP01_DreamDoorREF.SetOpen(False)
	MQP01_DreamDoorREF.SetLockLevel(255)
	MQ10a_SC1_MotherREF.Disable()
	PlayerREF.UnequipAll()
	MQ10a_SC1_SisterREF.Disable()
	MQP01_FatherRef.Disable()
	MQ10a_SC1_FatherREF.Disable()
	MQ12c_SC03_FatherREF.Disable()
	MQ18_Tombestone_01.Enable()
	MQ18_Tombestone_02.Enable()
	MQ18_Tombestone_03.Enable()
	MQP01_DreamDoorREF.BlockActivation(True)
	MQ18b_HouesLight.Disable()
	
	if bKatharsis
		MQ18_Tombestone_Katharsis.Enable()
		MQ18b_ActivatorREF.Enable()
	Else
		if MQ17.akCompanion == _00E_MC_CaliaREF
			_00E_MC_CaliaREF.MoveTo(MQ18a_CompanionMarker)
			Companion.ForceRefTo(_00E_MC_CaliaREF)
			_00E_MC_CaliaREF.EvaluatePackage()
		Else
			_00E_MC_JesparREF.MoveTo(MQ18a_CompanionMarker)
			Companion.ForceRefTo(_00E_MC_JesparREF)
			_00E_MC_JesparREF.EvaluatePackage()
		EndIf
	EndIf
			
	Utility.Wait(2)
	
	FadeToWhiteBackIMOD.ApplyCrossFade(afFadeDuration = 3.0)
	Game.SetPlayerAIDriven(False)
	Game.EnablePlayerControls()
	Game.DisablePlayerControls(false, true, true, false, true, false, false)
	
EndFunction

Function FloatAway()

	Sound.StopInstance(MQ17.iCleansingLoopSound)
	iWindLoop = _00E_AMB_WhispertreeWindLoopM.Play(PlayerREF)
	_00E_SilenceAbruptHighPriority.Add()
	MQ18b_SC01_WalkToGrave.ForceStart()
	RegisterForSingleUpdate(2)
	
EndFunction


;=====================================================================================
;              							PROPERTIES                    					 
;=====================================================================================

int iWindLoop

Actor Property PlayerREF Auto

_00E_MQ17_Functions Property MQ17 Auto
GlobalVariable Property AllowIdleChatter Auto

Actor Property MQ10a_SC1_FatherREF Auto
Actor Property MQ12c_SC03_FatherREF Auto
Actor Property MQP01_FatherRef Auto
Actor Property MQ10a_SC1_SisterREF Auto
Actor Property MQ10a_SC1_MotherREF Auto
Actor Property _00E_MC_CaliaREF Auto
Actor Property _00E_MC_JesparREF Auto

Message Property _00E_Game_PostCreditsMessage Auto

ReferenceAlias Property Companion Auto

ImageSpaceModifier Property FadeToWhiteBackIMOD Auto
ImageSpaceModifier Property FadeToWhiteHoldIMOD Auto
ImageSpaceModifier Property _00E_MQ18b_EndingIMOD Auto

ObjectReference Property PlayerStartMarkerNew Auto
ObjectReference Property MQ18_Linker Auto
ObjectReference Property MQP01_DreamDoorREF Auto
ObjectReference Property MQ18_Tombestone_01 Auto
ObjectReference Property MQ12a_SC3_BlackStone03 Auto
ObjectReference Property MQ12a_SC1_BlackStone02 Auto
ObjectReference Property MQ12a_SC1_BlackStone01 Auto
ObjectReference Property MQ18_Tombestone_02 Auto
ObjectReference Property MQ18_Tombestone_03 Auto
ObjectReference Property MQ18_Tombestone_Katharsis Auto
ObjectReference Property MQ18a_CompanionMarker Auto
ObjectReference Property MQ18b_FloatAwayMarker Auto
ObjectReference Property MQ18b_HouesLight Auto
ObjectReference Property MQ18b_ActivatorREF Auto

MusicType Property _00E_SilenceAbruptHighPriority Auto
MusicType Property _00E_Music_Special_MQ18b_Katharsis Auto

Scene Property MQ18b_SC01_WalkToGrave Auto

Sound Property _00E_AMB_WhispertreeWindLoopM Auto

Weather Property _00E_MQ18_EpilogueWeather Auto