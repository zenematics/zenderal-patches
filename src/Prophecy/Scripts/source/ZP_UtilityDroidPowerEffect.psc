Scriptname ZP_UtilityDroidPowerEffect extends ActiveMagicEffect
{Prophecy Gadgets - Utility Droid (lesser power, replaced Bear Traps 2026-10-23). One droid at a time:
  - the remembered droid (DroidList) still alive: it is called back to the player's side, free;
  - otherwise a new one is deployed. The first ever is free (FreeUsed, once per save); every later one costs Cost
    Spare Parts. Without them the power says so and does nothing.
The droid is Enderal's Starling Spider re-purposed (ZP_Prophecy_UtilityDroid): it follows the player on SureAI's
_DefaultFollowPlayer package, and its ability (ZP_UtilityDroidEffect) heals the player and staggers enemies.
Its Health is set here: BaseHealth + HealthPerLevel per player level.}

ActorBase Property Droid Auto
MiscObject Property SpareParts Auto
FormList Property DroidList Auto
GlobalVariable Property FreeUsed Auto
Int Property Cost = 10 Auto
Float Property BaseHealth = 100.0 Auto
Float Property HealthPerLevel = 10.0 Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Actor player = akCaster
	Actor current = None
	If DroidList.GetSize() > 0
		current = DroidList.GetAt(0) as Actor
	EndIf
	If current && !current.IsDead() && !current.IsDisabled()
		current.MoveTo(player, 96.0 * Math.Sin(player.GetAngleZ()), 96.0 * Math.Cos(player.GetAngleZ()), 0.0)
		Debug.Notification("Your Utility Droid returns to your side.")
		Return
	EndIf
	If FreeUsed.GetValue() == 0
		FreeUsed.SetValue(1)
	ElseIf player.GetItemCount(SpareParts) >= Cost
		player.RemoveItem(SpareParts, Cost)
	Else
		Debug.Notification("You need " + Cost + " Spare Parts to build a Utility Droid.")
		Return
	EndIf
	Actor d = player.PlaceActorAtMe(Droid)
	If !d
		Return
	EndIf
	d.SetActorValue("Health", BaseHealth + HealthPerLevel * player.GetLevel())
	d.RestoreActorValue("Health", 100000.0)
	d.SetPlayerTeammate(true)
	DroidList.Revert()
	DroidList.AddForm(d)
	Debug.Notification("Utility Droid deployed.")
EndEvent
