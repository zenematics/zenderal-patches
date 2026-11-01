Scriptname ZP_FlowStateEffect extends ActiveMagicEffect
{Flow State (Prophecy, Martial Arts capstone): a dodge in combat slows time briefly, once per SlowEvery, and sets off a
Shock Nova at the player's feet, once per NovaEvery (2026-10-23), with chain lightning cast at the player's
combat target (2026-10-29). The two cooldowns run independently.
Listens for TK Dodge RE's TKDR_DodgeStart animation event. Re-registers every 30 s because animation
event registrations do not survive every graph reload.}

Spell Property SlowTime Auto
Float Property Cooldown = 10.0 Auto          ; unused since 2026-10-29: a running effect keeps its saved value
Float Property SlowEvery = 8.0 Auto          ; new names, so saves pick up the defaults (curator: 8 s each)
Explosion Property Nova Auto
Float Property NovaCooldown = 15.0 Auto      ; unused, as Cooldown
Float Property NovaEvery = 8.0 Auto
Spell Property ChainLightning Auto            ; with the nova, at the combat target (2026-10-29)

Actor Player
Float NextReady
Float NextNova

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
	If !Player || !Player.IsInCombat()
		Return
	EndIf
	Float now = Utility.GetCurrentRealTime()
	If now >= NextReady
		NextReady = now + SlowEvery
		SlowTime.Cast(Player, Player)
	EndIf
	If !Nova
		; an effect started before the nova existed (2026-10-23) keeps Nova as None for the life of the save: look it up
		Nova = Game.GetFormFromFile(0x0000093D, "Zenderal - Prophecy.esp") as Explosion
	EndIf
	If !ChainLightning
		ChainLightning = Game.GetFormFromFile(0x00000B02, "Zenderal - Prophecy.esp") as Spell   ; likewise
	EndIf
	If Nova && now >= NextNova
		NextNova = now + NovaEvery
		Player.PlaceAtMe(Nova)
		Actor foe = Foe()
		If ChainLightning && foe
			ChainLightning.Cast(Player, foe)
		EndIf
	EndIf
EndEvent

; the player's combat target is often None (the player has no combat AI): then a living hostile within ~20 m
Actor Function Foe()
	Actor a = Player.GetCombatTarget()
	If a && !a.IsDead()
		Return a
	EndIf
	Int i = 0
	While i < 10
		a = Game.FindRandomActorFromRef(Player, 1400.0)
		If a && a != Player && !a.IsDead() && a.IsHostileToActor(Player)
			Return a
		EndIf
		i += 1
	EndWhile
	Return None
EndFunction

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	UnregisterForAnimationEvent(Player, "TKDR_DodgeStart")
	Player = None
EndEvent
