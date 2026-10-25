Scriptname _00E_MQP03_Functions extends Quest  

Import Utility
Import Game

int function _GetScriptVersion() Global
    return 2
endFunction

;=====================================================================================
;              							EVENTS                 					 
;=====================================================================================

Event OnUpdate()

	If (Self.GetCurrentStageID() < 20) && _00E_DisableMenuTutorials.GetValueInt() == 0
		If Game.UsingGamepad()
			_00E_MQP03_Tutorial_LeaveMenuHintConsole.ShowAsHelpMessage("_00E_MQP03_Tutorial_LeaveMenuHintConsole", 5, 1, 1)
		Else
			_00E_MQP03_Tutorial_LeaveMenuHint.ShowAsHelpMessage("_00E_MQP03_Tutorial_LeaveMenuHint", 5, 1, 1)
		EndIf
		RegisterForSingleUpdate(15)
	Else
		; Nothing
	EndIf

EndEvent

;=====================================================================================
;              							FUNCTIONS                 					 
;=====================================================================================

Function MovePlayerToStart()
	
	Debug.SendAnimationEvent(PlayerREF, "returnToDefault")
	_00E_SilenceAbruptHighPriority.Add()
	_00E_Func_AIWalk.PlayerAIWalkStop()
	FadeToBlackHoldIMOD.Apply()
	ForceFirstPerson()
	Game.DisablePlayerControls(abMovement = false, abFighting = true, abCamSwitch = true, abLooking = false, abSneaking = true, abMenu = true, abActivate = false, abJournalTabs = true, aiDisablePOVType = 0)
	PlayerREF.SetAlpha(0.0)
	PlayerREF.MoveTo(_00E_ClassMenuOrigin)
	SetCurrentStageID(10)
	
EndFunction

Function ShowVisionBinkMovie()
	
	If _00E_VideoSkip.GetValueInt() == 0 && EnderalFunctions.VideoSupport()
		; ZP: not interruptible - a key press ended it at once
		Game.PlayBink("MQP03NearDeathExperience.bik", false)
	EndIf
	Wait(2)
	FadeToBlackHoldIMOD.PopTo(_00E_MQP03_WakeUpIMOD)
	Wait(4)
	_00E_SilenceAbruptHighPriority.Remove()
	SetCurrentStageID(15)
EndFunction

function SetupPlayer()
	_00E_MQP03_Thoughts01.ShowAsHelpMessage("_00E_MQP03_Thoughts01", 5, 1, 1)
	Game.SetInCharGen(false, true, false)
	PlayerREF.AddShout(_00E_Class_Meditate)
	PlayerREF.EquipShout(_00E_Class_Meditate)
	Game.UnlockWord(_00E_Class_ClassMenuWord)
	Game.TeachWord(_00E_Class_ClassMenuWord)
	_00E_MQP03_sMemoryPointGained.Show(1)
	TalentPoints.SetValueInt(1)
	PlayerREF.SetActorValue("dragonsouls", TalentPoints.GetValueInt())
	RegisterForSingleUpdate(20)
endfunction

Function StrandingCutscene()

	Timescale.SetValue(10)
	AudioCategoryAMB.Unmute() 
	AudioCategoryAMB2x.Unmute() 
	AudioCategoryAMBr.Unmute() 
	_00E_PlayerFunctions.GetSafeItemRemove().RemoveAllItemsSafeVersion(None)	; Debug only!
	PlayerREF.AddItem(ClothesPrisonerRags, 1, True); Debug only!
	PlayerREF.EquipItem(ClothesPrisonerRags, false, true); Debug only!
	PlayerREF.MoveTo(MQP03_PlayerStrandingMarker)
	FadeToBlackHoldIMOD.Apply()
	DisablePlayerControls(True, True, True, True, True, True, True)
	PlayerREF.PlayIdle(Idle_1stPersonWoozyGetUpFromBed)
	FadeToBlackHoldIMOD.PopTo(_00E_WakeUp)
	Wait(9)
	_00E_WakeUp.PopTo(_00E_VisionHeadacheShort)
	PlayerREF.AddSpell(_00E_MQP03_MagicFeverSpell, False)
	MAGVampireSunlight.Play(PlayerREF)
	Game.EnablePlayerControls()
	_00E_MQP03_sFeelDizzy.Show()
	Wait(1)
	Self.SetCurrentStageID(25)
	
EndFunction

Function ShowThoughtBox()

	AudioCategoryAMB.Unmute() 
	AudioCategoryAMB2x.Unmute() 
	AudioCategoryAMBr.Unmute() 
	_00E_MQP03_Thoughts03.ShowAsHelpMessage("_00E_MQP03_Thoughts03", 5, 1, 1)

EndFunction

Function ShowEPTutorial()
	If _00E_DisableQuestTutorials.GetValueInt() == 0
		_00E_MQP03_Tutorial_EPSystem.Show()
	EndIf
EndFunction

Function ShowSkillbookTutorial()
	If _00E_DisableMenuTutorials.GetValueInt() == 0
		_00E_MQP03_Tutorial_Skillbooks.ShowAsHelpMessage("_00E_MQP03_Tutorial_Skillbooks", 4, 1, 1)
	EndIf
	Lernpunkte.SetValueInt(1)
	_00E_MQP03_sLearningPointGained.Show(1)
	Wait(6)
	If _00E_DisableMenuTutorials.GetValueInt() == 0
		_00E_MQP03_Tutorial_Skillbooks2.ShowAsHelpMessage("_00E_MQP03_Tutorial_Skillbooks2", 4, 1, 1)
	EndIf
EndFunction

Function ShowSleepTutorial()
	If _00E_DisableOtherTutorials.GetValueInt() == 0
		_00E_MQP03_Tutorial_Rest.ShowAsHelpMessage("_00E_MQP03_Tutorial_Rest", 5, 1, 1)
	EndIf
EndFunction


Function ShowThoughtBox05()

	_00E_MQP03_Thoughts05.ShowAsHelpMessage("_00E_MQP03_Thoughts05", 5, 1, 1)

EndFunction

Function ShowThoughtBox06()

	_00E_MQP03_Thoughts06.ShowAsHelpMessage("_00E_MQP03_Thoughts06", 5, 1, 1)

EndFunction

Function PrepareSoundAndWeather()

	_00E_SilenceAbruptHighPriority.Add()
	_00E_SuncoastSunrise.ForceActive()

EndFunction

Function FinishQuestAndStartMQ01()

	FXCameraAttachEmbersHeavyEffects.Stop(PlayerREF)
	FXCameraAttachEmbersEffect.Stop(PlayerREF)
	_00E_MQP03_Blendung_10.Apply()
	_00E_SilenceAbruptHighPriority.Remove()
	_00E_Music_Special_Act1Theme.Add()
	Self.SetObjectiveCompleted(5)
	MQ01.Start()
	MQ01.SetCurrentStageID(5)
	Wait(1)
	If _00E_DisableOtherTutorials.GetValueInt() == 0
		_00E_MQ01_Tutorial_FoodAndMushrooms.ShowAsHelpMessage("_00E_MQ01_Tutorial_FoodAndMushrooms", 5, 1, 1)
	EndIf
	
EndFunction

;=====================================================================================
;              							PROPERTIES                 					 
;=====================================================================================

Actor Property PlayerREF Auto

SoundCategory Property AudioCategoryAMB Auto
SoundCategory Property AudioCategoryAMB2x Auto
SoundCategory Property AudioCategoryAMBr Auto

MusicType Property _00E_Music_Special_Act1Theme Auto
MusicType Property _00E_SilenceAbruptHighPriority Auto

GlobalVariable Property _00E_DisableMenuTutorials Auto
GlobalVariable Property _00E_DisableQuestTutorials Auto
GlobalVariable Property _00E_DisableOtherTutorials Auto
GlobalVariable Property _00E_VideoSkip Auto
Weather Property _00E_SuncoastSunrise Auto

Message Property _00E_MQP03_sMemoryPointGained Auto
Message Property _00E_MQP03_sLearningPointGained Auto
Message Property _00E_MQP03_Tutorial_LeaveMenuHint Auto
Message Property _00E_MQP03_Tutorial_LeaveMenuHintConsole Auto
Message Property _00E_MQP03_Thoughts01 Auto
Message Property _00E_MQP03_Thoughts03 Auto
Message Property _00E_MQP03_Thoughts05 Auto
Message Property _00E_MQP03_sFeelDizzy Auto
Message Property _00E_MQP03_Thoughts06 Auto
Message Property _00E_MQP03_Tutorial_EPSystem Auto
Message Property _00E_MQP03_Tutorial_Rest Auto
Message Property _00E_MQ01_Tutorial_FoodAndMushrooms Auto
Message Property _00E_MQP03_Tutorial_Skillbooks Auto
Message Property _00E_MQP03_Tutorial_Skillbooks2 Auto
Idle Property Idle_1stPersonWoozyGetUpFromBed Auto

Armor Property ClothesPrisonerRags Auto

ImageSpaceModifier Property _00E_MQP03_Blendung_10 Auto

ObjectReference Property _00E_ClassMenuOrigin Auto
ObjectReference Property MQP03_PlayerStrandingMarker Auto

Quest Property MQ01 Auto

Sound Property MAGVampireSunlight Auto

GlobalVariable Property TalentPoints Auto
GlobalVariable Property Lernpunkte Auto
GlobalVariable Property Timescale Auto

Spell Property _00E_MQP03_MagicFeverSpell Auto

ImageSpaceModifier Property _00E_MQP03_WakeUpIMOD Auto
ImageSpaceModifier Property FadeToBlackHoldIMOD Auto
ImageSpaceModifier Property _00E_WakeUp Auto
ImageSpaceModifier Property _00E_VisionHeadacheShort Auto

WordOfPower Property _00E_Class_ClassMenuWord Auto
Shout Property _00E_Class_Meditate Auto

VisualEffect Property FXCameraAttachEmbersHeavyEffects Auto
VisualEffect Property FXCameraAttachEmbersEffect Auto
