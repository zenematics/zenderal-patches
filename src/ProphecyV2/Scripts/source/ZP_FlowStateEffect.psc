Scriptname ZP_FlowStateEffect extends ActiveMagicEffect
{Flow State (Prophecy, Martial Arts capstone): a dodge in combat slows time briefly, once per cooldown.
Listens for TK Dodge RE's TKDR_DodgeStart animation event. Re-registers every 30 s because animation
event registrations do not survive every graph reload.}

Spell Property SlowTime Auto
Float Property Cooldown = 10.0 Auto

Actor Player
Float NextReady

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Player = akTarget
	RegisterForAnimationEvent(Player, "TKDR_DodgeStart")
	RegisterForSingleUpdate(30.0)
EndEvent

Event OnUpdate()
	If Player
		RegisterForAnimationEvent(Player, "TKDR_DodgeStart")
		RegisterForSingleUpdate(30.0)
	EndIf
EndEvent

Event OnAnimationEvent(ObjectReference akSource, string asEventName)
	Float now = Utility.GetCurrentRealTime()
	If Player.IsInCombat() && now >= NextReady
		NextReady = now + Cooldown
		SlowTime.Cast(Player, Player)
	EndIf
EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	UnregisterForAnimationEvent(Player, "TKDR_DodgeStart")
	Player = None
EndEvent
