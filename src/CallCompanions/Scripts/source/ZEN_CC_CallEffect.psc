Scriptname ZEN_CC_CallEffect extends ActiveMagicEffect
{Call Companions - the lesser power. Moves every player teammate (Enderal's companions are SetPlayerTeammate actors,
see _00E_Func_SetNPCAsCompanion; hirelings and Prophecy's Legion skeletons too) and every actor the player commands
(conjured summons) into an arc behind the player. Loaded teammates come from PO3's GetPlayerFollowers (high process
only); each one is remembered in Known, so a companion left behind in an unloaded cell is still called next time,
as long as it is still a teammate. Skipped: the dead, the disabled, actors told to wait (WaitingForPlayer), actors
in a scene, mounted actors, anyone already within CloseEnough, and Prophecy's Andrasta's Owl (script-flown).}

FormList Property Known Auto

Float Property CloseEnough = 400.0 Auto
Float Property Distance = 120.0 Auto

Actor player
Form owlBase
Int moved

Event OnEffectStart(Actor akTarget, Actor akCaster)
	player = Game.GetPlayer()
	owlBase = Game.GetFormFromFile(0x97F, "Zenderal - Prophecy.esp")   ; ZP_Prophecy_SendOwl_Owl - soft, no master
	moved = 0

	Actor[] followers = PO3_SKSEFunctions.GetPlayerFollowers()
	Int i = 0
	While i < followers.Length
		Actor a = followers[i]
		If a && a.IsPlayerTeammate() && !a.IsDead()
			If !Known.HasForm(a)
				Known.AddForm(a)
			EndIf
			Call(a)
		EndIf
		i += 1
	EndWhile

	Actor[] summons = PO3_SKSEFunctions.GetCommandedActors(player)
	i = 0
	While i < summons.Length
		Call(summons[i])
		i += 1
	EndWhile

	; Remembered companions not in the high process; drop the ones that are gone or no longer teammates
	i = Known.GetSize() - 1
	While i >= 0
		Actor k = Known.GetAt(i) as Actor
		If !k || k.IsDead() || !k.IsPlayerTeammate()
			Known.RemoveAddedForm(Known.GetAt(i))
		Else
			Call(k)
		EndIf
		i -= 1
	EndWhile

	If moved == 0
		Debug.Notification("No companions to call.")
	ElseIf moved == 1
		Debug.Notification("Called 1 companion.")
	Else
		Debug.Notification("Called " + moved + " companions.")
	EndIf
EndEvent

Function Call(Actor a)
	If !a || a == player || a.IsDead() || a.IsDisabled()
		Return
	EndIf
	If owlBase && a.GetActorBase() == owlBase
		Return
	EndIf
	If a.GetActorValue("WaitingForPlayer") > 0 || a.GetCurrentScene() || a.IsOnMount()
		Return
	EndIf
	If a.Is3DLoaded() && a.GetParentCell() == player.GetParentCell() && a.GetDistance(player) < CloseEnough
		Return
	EndIf
	; behind the player, spread 30 degrees apart
	Float ang = player.GetAngleZ() + 180.0
	Int slot = moved % 7
	If slot % 2 == 1
		ang += 15.0 * (slot + 1)
	Else
		ang -= 15.0 * slot
	EndIf
	a.MoveTo(player, Distance * Math.Sin(ang), Distance * Math.Cos(ang), 0.0, False)
	a.SetAngle(0.0, 0.0, player.GetAngleZ())
	a.EvaluatePackage()
	moved += 1
EndFunction
