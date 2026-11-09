Scriptname _00E_Class_OpenClassMenuScript extends activemagiceffect  

Import Utility
Import Game

;=====================================================================================
;              							EVENTS                  					 
;=====================================================================================

Event OnEffectStart(Actor TheTarget, Actor TheCaster)
	; Enderal Together (co-op): only the player who cast the meditation enters the meditation temple.
	; Merged by Zenderal into Meditation Area v2.1.0 3rd Person POV Unlock's version (Nexus 683, f1.01).
	If TheCaster != Game.GetPlayer()
		Return
	EndIf
	If _00E_Meditate_PlayerIsTeleporting.GetValue() != 0
		Return
	EndIf
	_00E_Meditate_PlayerIsTeleporting.SetValue(1)
	
	Bool bDoSettleDownWait = True

	If (MQP03.GetCurrentStageID() <= 15) && (MQP03.IsRunning())
	
		_00E_Class_MenuIMODIntro.Apply()
		Wait(0.5)
		PlayerREF.MoveTo(MQP03_PlayerStartMarker)
		PlayerREF.SetAlpha(1.0)
		MQP03.SetCurrentStageID(20)
		
	Else
	
		if !(PlayerREF.IsInLocation(_00E_ClassMenuLocation))
			If PlayerREF.GetRace() == _00E_Theriantrophist_PlayerWerewolfRace || _00E_Meditate_Allowed.GetValueInt() == 0
				_00E_Meditation_sCantMeditateNow.Show()
				bDoSettleDownWait = False
			ElseIf PlayerREF.IsInCombat()
				_00E_Meditation_sCantMeditateWithEnemies.Show()
				bDoSettleDownWait = False
			Else
				EnterClassMenu()
			EndIf
		else	
			ExitClassMenu()
		endif
		
	EndIf

	If bDoSettleDownWait ; Give a few moments for things to settle down before allowing another teleport
		Wait(0.75)
	EndIf

	_00E_Meditate_PlayerIsTeleporting.SetValue(0)

EndEvent


;=====================================================================================
;              							FUNCTIONS                  					 
;=====================================================================================

Function EnterClassMenu()
	
																																																		   
	
	Player.ForceRefTo(PlayerREF)
	
	_00E_EquipControl.SheatheWeapon(PlayerREF, false)

	Form[] equippedTorches = New Form[2]
	_00E_TorchControl.UnequipTorches(equippedTorches)

	_00E_RealWorldOrigin.MoveTo(playerREF)
	_00E_Class_MenuMeditationSound.Play(PlayerREF)
	_00E_Class_MenuIMODIntro.Apply()
	Wait(0.7)
	PlayerREF.MoveTo(_00E_ClassMenuOrigin)
									
				   
	
EndFunction

Function ExitClassMenu()

	_00E_Class_MenuMeditationSound.Play(PlayerREF)
	_00E_Class_MenuIMODIntro.Apply()
	Wait(0.7)
	PlayerREF.MoveTo(_00E_RealWorldOrigin)
	PlayerREF.SetAlpha(1.0)
	Player.Clear()
	Game.EnablePlayerControls()
	Game.ShowFirstPersonGeometry(True)
												
						 
	  
	Game.RequestAutoSave()
	
EndFunction

;=====================================================================================
;              							PROPERTIES                  					 
;=====================================================================================

Actor Property PlayerREF Auto
ImagespaceModifier Property _00E_Class_MenuIMODIntro Auto

Quest Property MQP03 Auto

Sound Property _00E_Class_MenuMeditationSound Auto
Location property _00E_ClassMenuLocation Auto
ObjectReference Property _00E_ClassMenuOrigin Auto
ObjectReference Property _00E_RealWorldOrigin Auto
ObjectReference Property MQP03_PlayerStartMarker Auto

Message Property _00E_Meditation_sCantMeditateWithEnemies Auto
Message Property _00E_Meditation_sCantMeditateNow Auto

GlobalVariable Property _00E_Meditate_PlayerIsTeleporting Auto
GlobalVariable Property _00E_Meditate_Allowed Auto

ReferenceAlias Property Player Auto

Race Property _00E_Theriantrophist_PlayerWerewolfRace Auto
