Scriptname _00E_MQ18a_Functions extends Quest 

Import Utility

int function _GetScriptVersion() Global
    return 1
endFunction

;=====================================================================================
;              							FUNCTIONS                    					 
;=====================================================================================

Function SetUpCompanion()

	if MQ17.akCompanion == _00E_MC_CaliaREF
		akCompanion = _00E_MC_CaliaREF
		Companion.ForceRefTo(_00E_MC_CaliaREF)
	Else
		akCompanion = _00E_MC_JesparREF
		Companion.ForceRefTo(_00E_MC_JesparREF)
	EndIf
	
	if akCompanion.IsDisabled()
		akCompanion.Enable()
	EndIf
	
	akCompanion.BlockActivation(True)
	MQ18a_SC01_DreamSequence.ForceStart()

EndFunction

Function PortCompanion(Objectreference objPortTarget)

	TimeFadeOut01FXS.Play(akCompanion)
	Wait(2)
	MAGConjurePortalClose.Play(akCompanion)
	akCompanion.MoveTo(objPortTarget)
	TimeFadeIn01FXS.Play(akCompanion)
	
EndFunction

Function FadeOutDream()

	FadeToWhiteImod.Apply()
	Wait(2)
	Game.DisablePlayerControls()
	FadeToWhiteHoldImod.ApplyCrossFade(afFadeDuration = 1.0)
	Wait(4)
	Weather.ReleaseOverride()
	PlayerREF.SetScale(1)
	SetCurrentStageID(20)
	
EndFunction

Function StartSC02()

	_00E_PlayerFunctions.GetSafeItemRemove().RemoveAllitemsSafeVersion(None)
	
	_00E_StarCityWeather.ForceActive(True)
	_00E_BloodyFXShader.Stop(PlayerREF)
	Game.ForceFirstPerson()
	_00E_TimeControl.SkipTimeToHour(18.4)
	PlayerREF.SetAngle(MQ18a_SC02_PlayerWakeUpREF.GetAngleX(), MQ18a_SC02_PlayerWakeUpREF.GetAngleY(), MQ18a_SC02_PlayerWakeUpREF.GetAngleZ())
	PlayerREF.MoveTo(MQ18a_SC02_WakeUpMarker)
	PlayerREF.PlayIdle(TG05_Knockout)

	akCompanion.MoveTo(MQ18a_SC02_CompanionSitLedgeMarker)
	TimeFadeIn01FXS.Play(akCompanion)
	akCompanion.BlockActivation(False)
	
	MQ18a_SC02_StarCity.ForceStart()
	
EndFunction

Function StartSC02_Failsave()

	If !MQ18a_SC02_StarCity.IsPlaying()
		MQ18a_SC02_StarCity.ForceStart()
	EndIf

EndFunction

Function WakeUp()

	Game.ShowFirstPersonGeometry(True)
	PlayerREF.SetOutfit(MinerClothesOutfit02)
	PlayerREF.DispelAllSpells()
	PlayerREF.PlayIdle(TG05_GetUp)
	_00E_MQ18a_WakeUpImod.ApplyCrossFade(afFadeDuration = 3.0)
	Wait(3)
	Game.EnablePlayerControls()
	MQ18a_SC02_PlayerWakeUpREF.BlockActivation(True)
	
EndFunction

Function StartMusic()

	_00E_PlayerFunctions.GetSoundControl().RemoveSilence()
	_00E_Music_Special_Ending_BraveNewWorld.Add()

EndFunction

Function SlowSpeed()

	Game.ForceThirdPerson()
	PlayerREF.SetActorValue("speedMult", 75)
	_00E_PlayerFunctions.GetVisionControl().UpdateSpeed(PlayerREF)

EndFunction

Function ShowCredits()

	Debug.ToggleMenus()
	Steam.UnlockAchievement("END_COMPLETE_MQ18A_01")
	FadeToBlackHoldIMOD.Apply()
	Wait(8)
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

Actor Property akCompanion Auto Hidden

Actor Property _00E_MC_CaliaREF Auto
Actor Property _00E_MC_JesparREF Auto
Actor Property PlayerREF Auto

_00E_MQ17_Functions Property MQ17 Auto

EffectShader Property TimeFadeOut01FXS Auto
EffectShader Property TimeFadeIn01FXS Auto
EffectShader Property _00E_BloodyFXShader Auto

Scene Property MQ18a_SC01_DreamSequence Auto
Scene Property MQ18a_SC02_StarCity Auto

Outfit Property MinerClothesOutfit02 Auto

Sound Property MAGConjurePortalClose Auto

Message Property _00E_Game_PostCreditsMessage Auto

ReferenceAlias Property Companion Auto
 
Idle Property TG05_Knockout Auto
Idle Property TG05_GetUp Auto

MusicType Property _00E_Music_Special_Ending_BraveNewWorld Auto

Weather Property _00E_StarCityWeather Auto

ImageSpaceModifier Property FadeToWhiteImod Auto
ImageSpaceModifier Property FadeToWhiteHoldImod Auto
ImageSpaceModifier Property _00E_MQ18a_WakeUpImod Auto
ImageSpaceModifier Property FadeToBlackHoldIMOD Auto

ObjectReference Property MQ18a_Companion_001 Auto
ObjectReference Property MQ18a_Companion_002 Auto
ObjectReference Property MQ18a_Companion_003 Auto
ObjectReference Property MQ18a_Companion_004 Auto
ObjectReference Property MQ18a_Companion_005 Auto
ObjectReference Property MQ18a_SC02_PlayerWakeUpREF Auto
ObjectReference Property MQ18a_SC02_CompanionSitLedgeMarker Auto
ObjectReference Property MQ18a_SC02_WakeUpMarker Auto