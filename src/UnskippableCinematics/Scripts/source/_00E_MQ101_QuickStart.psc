Scriptname _00E_MQ101_QuickStart extends Quest  

function Init()

	MQP01.CompleteAllObjectives()
	MQP01.CompleteQuest()
	MQP01.Stop()
	
	MQP02.CompleteAllObjectives()
	MQP02.CompleteQuest()
	MQP02.Stop()

	Utility.wait(0.5)

	If _00E_VideoSkip.GetValueInt() == 0 && EnderalFunctions.VideoSupport()
		; ZP: not interruptible - a key press ended it at once
		Game.PlayBink("MQP03NearDeathExperience.bik", false)
	EndIf

	Actor PlayerREF = Game.GetForm(0x14) as Actor
	PlayerREF.MoveTo(_00E_ClassMenuOrigin)

	Debug.SendAnimationEvent(PlayerRef, "IdleForceDefaultState")
	Utility.Wait(0.5)
	Game.ShowRaceMenu()
	
	Utility.Wait(0.1)

	Game.DisablePlayerControls(abMovement = false, abFighting = true, abCamSwitch = true, abLooking = false, abSneaking = true, abMenu = true, abActivate = false, abJournalTabs = true, aiDisablePOVType = 0)
	Game.ForceFirstPerson()

	(MQP02 as _00E_MQP02_Functions).AddRacialAbilites()
	
	MQP03.SetCurrentStageID(15)

endfunction

Quest Property MQP01  Auto  
Quest Property MQP02  Auto  
Quest Property MQP03  Auto  

GlobalVariable Property _00E_VideoSkip  Auto  

ObjectReference Property _00E_ClassMenuOrigin  Auto  
