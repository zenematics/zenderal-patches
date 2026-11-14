Scriptname _00E_MQP02_RopeSC extends ObjectReference
{Zenderal fork of SureAI's rope activator script (MQP02 "A New Life", objective "Find a rope").
SureAI's OnActivate is unchanged. Added: a watchdog that traces the Veiled Woman scene that the rope
starts, and unsticks the two places where the player can stay AI-driven forever:
 - the player's AI walk to the crate marker (MQP02_SC4_PlayerAIWalkToCrate 07B8F6, radius 8);
 - the levitation chain (stage 75), which only advances on the player alias's
   OnTranslationAlmostComplete: a SplineTranslateTo that never nears its end hangs it.
No property added or removed. Log lines start with [ZP MQP02 rope].}

Event OnActivate(ObjectReference akActionRef)

	If MQP02_SC4_VeiledWomanAppears.IsActionComplete(33)
		MQP02.SetActivationRopeBool()
		ZP_StartWatchdog()
	Else
		Debug.Trace("[ZP MQP02 rope] activated before Sirius's forcegreet (scene action 33) finished: ignored, as in SureAI's script. Stage " + MQP02.GetCurrentStageID() + ", scene playing " + MQP02_SC4_VeiledWomanAppears.IsPlaying())
	EndIf

EndEvent

_00E_MQP02_Functions Property MQP02 Auto

Scene Property MQP02_SC4_VeiledWomanAppears Auto

; ---------------------------------------------------------------------------------------------
; Zenderal watchdog (no properties: forms are looked up by FormID)
; ---------------------------------------------------------------------------------------------

Bool ZP_bWatching = False
Int ZP_iTicks = 0
Int ZP_iLastStage = -1
Int ZP_iStageTicks = 0
Int ZP_iWalkTicks = 0
Int ZP_iLevitateTicks = 0
Int ZP_iScreamTicks = 0
Bool ZP_bWalkFixed = False
Bool ZP_bDashFixed = False
Bool ZP_bKnockOutFixed = False

; tick 1 s; walk limit 20 s after "Find a rope" completes; levitation limit 25 s (the rise takes ~9 s);
; knockout limit 10 s after the dash (SureAI's knockout runs ~4 s after it); STALL line after 60 s on one stage

Function ZP_StartWatchdog()
	If ZP_bWatching
		Return
	EndIf
	ZP_bWatching = True
	ZP_iTicks = 0
	Debug.Trace("[ZP MQP02 rope] rope accepted: watchdog started. " + ZP_State())
	RegisterForSingleUpdate(1.0)
EndFunction

String Function ZP_State()
	Actor player = Game.GetPlayer()
	ObjectReference crate = Game.GetFormFromFile(0x07BB5A, "Skyrim.esm") as ObjectReference
	Actor sirius = Game.GetFormFromFile(0x0775F5, "Skyrim.esm") as Actor
	Scene sc = MQP02_SC4_VeiledWomanAppears
	String s = "stage " + MQP02.GetCurrentStageID() + " scene " + sc.IsPlaying()
	s += " obj10done " + MQP02.IsObjectiveCompleted(10)
	s += " act2 " + sc.IsActionComplete(2) + " act4 " + sc.IsActionComplete(4) + " act18 " + sc.IsActionComplete(18) + " act42 " + sc.IsActionComplete(42)
	s += " lev " + MQP02.bIsLevitating + " scream " + MQP02.bTimeToScream
	s += " player " + (player.GetPositionX() as Int) + "," + (player.GetPositionY() as Int) + "," + (player.GetPositionZ() as Int)
	If crate
		s += " toCrate " + (player.GetDistance(crate) as Int)
	EndIf
	If sirius
		s += " siriusSit " + sirius.GetSitState()
	EndIf
	Return s
EndFunction

Event OnUpdate()
	If !ZP_bWatching
		Return
	EndIf
	; register first: an error below must not end the watchdog
	RegisterForSingleUpdate(1.0)
	ZP_iTicks += 1

	Int stage = MQP02.GetCurrentStageID()
	If stage >= 80
		ZP_bWatching = False
		UnregisterForUpdate()
		Debug.Trace("[ZP MQP02 rope] stage " + stage + " reached after " + ZP_iTicks + " s: watchdog done.")
		Return
	EndIf

	If stage != ZP_iLastStage
		Debug.Trace("[ZP MQP02 rope] t=" + ZP_iTicks + " stage " + ZP_iLastStage + " -> " + stage + ". " + ZP_State())
		ZP_iLastStage = stage
		ZP_iStageTicks = 0
	Else
		ZP_iStageTicks += 1
	EndIf
	If ZP_iTicks % 5 == 0
		Debug.Trace("[ZP MQP02 rope] t=" + ZP_iTicks + " " + ZP_State())
	EndIf

	Actor player = Game.GetPlayer()

	; 1) the AI walk to the crate (phase 2 completed = objective 10 completed; player AI-driven)
	If stage < 72 && !ZP_bWalkFixed && MQP02.IsObjectiveCompleted(10)
		ObjectReference crate = Game.GetFormFromFile(0x07BB5A, "Skyrim.esm") as ObjectReference
		If crate && player.GetDistance(crate) > 32.0
			ZP_iWalkTicks += 1
			If ZP_iWalkTicks >= 20
				ZP_bWalkFixed = True
				Debug.Trace("[ZP MQP02 rope] FIX walk: player still " + (player.GetDistance(crate) as Int) + " units from MQP02_SC4_PlayerWalkToMarker after " + ZP_iWalkTicks + " s; moving them onto it. " + ZP_State())
				player.MoveTo(crate)
			EndIf
		EndIf
	EndIf

	; 2) the levitation chain (stage 75)
	If stage == 75
		If MQP02.bIsLevitating && !MQP02.bTimeToScream && !ZP_bDashFixed
			ZP_iLevitateTicks += 1
			If ZP_iLevitateTicks >= 25
				ZP_bDashFixed = True
				Debug.Trace("[ZP MQP02 rope] FIX levitation: the rise never reported near completion in " + ZP_iLevitateTicks + " s; ending it and starting SureAI's dash. " + ZP_State())
				player.StopTranslation()
				MQP02.DashPlayerTowardsWall()
			EndIf
		ElseIf MQP02.bTimeToScream && !ZP_bKnockOutFixed
			ZP_iScreamTicks += 1
			If ZP_iScreamTicks >= 10
				ZP_bKnockOutFixed = True
				Debug.Trace("[ZP MQP02 rope] FIX knockout: the dash never reported near completion in " + ZP_iScreamTicks + " s; ending it and running SureAI's knockout. " + ZP_State())
				player.StopTranslation()
				MQP02.KnockOutPlayer()
			EndIf
		EndIf
	EndIf

	If ZP_iStageTicks == 60
		Debug.Trace("[ZP MQP02 rope] STALL: stage " + stage + " for " + ZP_iStageTicks + " s. " + ZP_State())
	EndIf
EndEvent
