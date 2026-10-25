Scriptname _00E_MQP01_Functions extends Quest  

Import Utility

int function _GetScriptVersion() Global
    return 1
endFunction

;=====================================================================================
;              							FUNCTIONS                  					 
;=====================================================================================

Function SetUpScene()

	Game.FadeOutGame(false, true, 0.5, 0.5)
	FadeToBlackHoldIMOD.Apply()
	PlayerREF.SetScale(0.85)
	TimeScale.SetValue(0.1)
	GameHour.SetValue(18.5)
	Game.ForceFirstPerson()
	Game.DisablePlayerControls(false, true, true, false, true, false, false)
	FadeToBlackBackImod.Apply()
	FadeToBlackHoldIMOD.Remove()
	MQP01_DreamDoorREF.BlockActivation(True)
	Wait(5.0)
	
EndFunction

Function UnlockDoor()

	MQP01_DreamDoorREF.Lock(False)
	MQP01_DreamDoorREF.BlockActivation(False)
	
EndFunction

Function UnblockDoor()

	MQP01_DreamDoorREF.BlockActivation(False)

EndFunction

Function ArriveInHouse()

	_00E_MQP01_InfantLaughing.Play(PlayerREF)
	TimeScale.SetValue(450)
	RegisterForSingleUpdate(1)

EndFunction

Function SC01_FatherFailsave()

	Game.DisablePlayerControls()

	if MQP01_FatherREF.GetDistance(MQP01_SC1_FatherArriveMarker) >= 75 
		MQP01_FatherREF.MoveTo(MQP01_SC1_FatherArriveMarker)
	EndIf

EndFunction

Function StartFatherWhistleScene()

	Game.DisablePlayerControls()
	MQP01_FatherREF.MoveTo(MQP01_SC1_FatherStartWalkingMarker)
	MQP01_SC1_FatherArrivesInKitchen.ForceStart()
	
EndFunction

Function StopMusic()

	_00E_SilenceTransitionHighPriority.Add()

EndFunction

Function  StartFatherAccuseScene()
	
	if PlayerREF.GetDistance(MQP01_SC01_PlayerWalkMarker) >= 55
		PlayerREF.TranslateToRef(MQP01_SC01_PlayerWalkMarker, 50, 50)
	EndIf
	
	AudioCategoryAMBr.SetVolume(__Config_MuteAmbienceVolume)
	AudioCategoryAMB.SetVolume(__Config_MuteAmbienceVolume)
	
	;AudioCategoryMUS.SetVolume(3.25)
	;AudioCategoryVOCGeneral.SetVolume(7.5)
	
	; Eddoursul: Instead of setting volume to 1, deafening some users, use relative values
	if SKSE.GetVersion() > 0
		fMusicVolume = Utility.GetINIfloat("fVal3:AudioMenu")
		fVoiceVolume = Utility.GetINIfloat("fVal1:AudioMenu")
		fEffectsVolume = Utility.GetINIfloat("fVal4:AudioMenu")
		
		AudioCategorySFX.SetVolume(fEffectsVolume * 0.75)
		AudioCategoryMUS.SetVolume(fMusicVolume * 1.20)
		
		if fVoiceVolume <= fMusicVolume
			AudioCategoryVOCGeneral.SetVolume(fMusicVolume * 1.25)
		else
			AudioCategoryVOCGeneral.SetVolume(fVoiceVolume * 1.15)
		endif
	endif
	
	_00E_Music_Special_Dreams.Remove()
	_00E_SilenceTransitionHighPriority.Remove()
	_00E_Music_Special_MQP01_BuildUp.Add()
	FireSound = FXFireEmbers02LP.Play(PlayerREF)
	MQP01_SC2_EmbersEffect01.Enable()
	MQP01_SC2_FatherAccusesThePlayer.ForceStart()
	
EndFunction

Function StartFire()

	Game.ShakeCamera()
	ExplosionToDisable00 = MQP01_SC2_ExplosionSpawnMarker.PlaceAtMe(_00E_HarmlessFireExplosion, 1)
	ExplosionToDisable01 = MQP01_FatherREF.PlaceAtMe(_00E_MQP01_IntenseFire, 1)
	MAGFireBallExpImod.Apply()
	MQP01_SC2_FireREF03.EnableNoWait()
	MQP01_SC2_FireREF04.EnableNoWait()
	MAGDestructionFireStormExplosionM.Play(PlayerREF)
	Wait(0.5)
	Game.ShakeCamera(afStrength = 0.7)
	MQP01_SC2_FireREF05.EnableNoWait()
	MQP01_SC2_FireREF06.EnableNoWait()
	MAGDestructionFireballExplosionM.Play(PlayerREF)
	FireFXShader.Play(MQP01_FatherRef)
	FireFXShader.Play(MQP01_SC02_Elk)
	Wait(0.5)
	BFXFireImod.Apply()
	MAGFirebolt03Fire.Play(PlayerREF)
	Game.ShakeCamera(afStrength = 0.1)
	MQP01_SC2_FireREF01.EnableNoWait()
	MQP01_SC2_FireREF02.EnableNoWait()
	_00E_MAGFXFireOilIgniteLow.Play(PlayerREF)
	MQP01_SC2_SmokeREF01.EnableNoWait()
	MQP01_SC2_EmbersEffect02.EnableNoWait()

EndFunction

Function FatherStartFeeding()

	_00E_MQP01_DevourElkM.Play(PlayerREF)
	MQP01_FatherREF.SetAnimationVariableBool("bAnimationDriven", true)
	Debug.SendAnimationEvent(MQP01_FatherREF, "IdleCannibalFeedCrouching")
	
EndFunction

Function CrashDownEverything()

	MQP01_SC02_Elk.PlayImpactEffect(BloodSprayImpactSetRed )
	Wait(0.5)
	MQP01_SC02_Elk.PlayImpactEffect(BloodSprayImpactSetRed )
	Wait(0.5)
	MQP01_SC02_Elk.PlayImpactEffect(BloodSprayImpactSetRed )
	Wait(0.5)
	MQP01_SC02_Elk.PlayImpactEffect(BloodSprayImpactSetRed )
	Wait(0.5)
	MQP01_SC02_Elk.PlayImpactEffect(BloodSprayImpactSetRed )
	Wait(0.5)
	MQP01_SC02_Elk.PlayImpactEffect(BloodSprayImpactSetRed )
	Wait(0.5)
	MQP01_SC02_Elk.PlayImpactEffect(BloodSprayImpactSetRed )
	Wait(0.5)
	MQP01_SC02_Elk.PlayImpactEffect(BloodSprayImpactSetRed )
	Wait(0.5)
	MQP01_SC02_Elk.PlayImpactEffect(BloodSprayImpactSetRed )
	Wait(0.5)
	MQP01_SC02_Elk.PlayImpactEffect(BloodSprayImpactSetRed )
	Wait(5.9)
	PlayerREF.TranslateToRef(MQP01_SC2_PlayerCameraTran, 1000.0, 1000.0)

EndFunction



Function PlayIntroAndMovePlayerToShip()

	AudioCategoryAMB.Mute()
	AudioCategoryMAG.Mute()
	AudioCategorySFX.Mute()
	MQP01_SC2_FatherAccusesThePlayer.Stop()
	_00E_SilenceAbruptHighPriority.Remove()
	PlayerREF.SetScale(1)
	Sound.StopInstance(FireSound)
	BFXFireImod.Remove()
	Wait(7.8)
	Steam.UnlockAchievement("END_COMPLETE_MQP01_01")
	If _00E_VideoSkip.GetValueInt() == 0 && EnderalFunctions.VideoSupport()
		; ZP: not interruptible - a key press ended it at once
		Game.PlayBink("EnderalIntro.bik", false)
	EndIf
	wait(0.2)
	
	; Eddoursul: restore the original volume level
	if SKSE.GetVersion() > 0
		AudioCategoryVOCGeneral.SetVolume(fVoiceVolume)
		AudioCategoryMUS.SetVolume(fMusicVolume)
		AudioCategorySFX.SetVolume(fEffectsVolume)
	endif
	
	AudioCategoryAMBr.SetVolume(1)
	AudioCategoryAMB.SetVolume(1)
	MQP02.SetCurrentStageID(5)
	AudioCategoryAMB.UnMute()
	AudioCategoryMAG.UnMute()
	AudioCategorySFX.UnMute()
	_00E_SilenceAbruptHighPriority.Remove()
	_00E_Music_Special_Dreams.Remove()
	ExplosionToDisable00.delete()
	ExplosionToDisable01.delete()

EndFunction

;=====================================================================================
;              							EVENTS                 					 
;=====================================================================================

Event OnUpdate()

	If (GameHour.GetValue() <= 22)
		RegisterForSingleUpdate(0.5)
	Else
		Timescale.SetValue(0.1)
	EndIf

EndEvent

;=====================================================================================
;              							PROPERTIES                  					 
;=====================================================================================

int iVOCGeneralValue
int FireSound
ObjectReference ExplosionToDisable00
ObjectReference ExplosionToDisable01

float Property __Config_MuteAmbienceVolume = 0.75 Auto
{At which level should the ambience sound be played? (0.5 -> 50% of normal loudness)}

float fMusicVolume = 0.75
float fVoiceVolume = 0.75
float fEffectsVolume = 0.75

MusicType Property _00E_Music_Special_Dreams Auto
MusicType Property _00E_SilenceAbruptHighPriority Auto
MusicType Property _00E_Music_Special_MQP01_BuildUp Auto
MusicType Property _00E_SilenceTransitionHighPriority Auto

Explosion Property _00E_HarmlessFireExplosion Auto

SoundCategory Property AudioCategoryVOCGeneral Auto
SoundCategory Property AudioCategoryAMB Auto
SoundCategory Property AudioCategoryMAG Auto
SoundCategory Property AudioCategorySFX Auto
SoundCategory Property AudioCategoryMUS Auto
SoundCategory Property AudioCategoryAMBr Auto

Actor Property PlayerREF Auto
Actor Property MQP01_FatherRef Auto

Scene Property MQP01_SC1_FatherArrivesInKitchen Auto
Scene Property MQP01_SC2_FatherAccusesThePlayer Auto

Sound Property _00E_MAGFXFireOilIgniteLow Auto
Sound Property _00E_MQP01_InfantLaughing Auto
Sound Property FXFireEmbers02LP Auto
Sound Property MAGDestructionFireStormExplosionM Auto
Sound Property MAGDestructionFireballExplosionM Auto
Sound Property MAGFirebolt03Fire Auto
Sound Property _00E_MQP01_DevourElkM Auto

ImpactDataSet Property BloodSprayImpactSetRed Auto

EffectShader Property FireFXShader Auto

Light Property _00E_MQP01_IntenseFire Auto

ObjectReference Property MQP01_SC1_FatherStartWalkingMarker Auto
ObjectReference Property MQP01_SC2_EmbersEffect01 Auto
ObjectReference Property MQP01_SC2_EmbersEffect02 Auto
ObjectReference Property MQP01_SC2_SmokeREF01 Auto
ObjectReference Property MQP01_SC2_FireREF01 Auto
ObjectReference Property MQP01_SC2_FireREF02 Auto
ObjectReference Property MQP01_SC2_FireREF03 Auto
ObjectReference Property MQP01_SC2_FireREF04 Auto
ObjectReference Property MQP01_SC2_FireREF05 Auto
ObjectReference Property MQP01_SC2_FireREF06 Auto
ObjectReference Property MQP01_SC2_ExplosionSpawnMarker Auto
ObjectReference Property MQP01_SC2_PlayerCameraTran Auto
ObjectReference Property MQP01_DreamDoorREF Auto
ObjectReference Property MQP01_SC02_Elk Auto
ObjectReference Property MQP01_SC1_FatherArriveMarker Auto
ObjectReference Property MQP01_SC01_PlayerWalkMarker Auto

Quest Property MQP02 Auto

GlobalVariable Property Timescale Auto
GlobalVariable Property GameHour Auto
GlobalVariable Property _00E_VideoSkip Auto

ImageSpaceModifier Property FadeToBlackHoldIMOD Auto
ImageSpaceModifier Property FadeToBlackBackImod Auto
ImageSpaceModifier Property MAGFireBallExpImod Auto
ImageSpaceModifier Property BFXFireImod Auto