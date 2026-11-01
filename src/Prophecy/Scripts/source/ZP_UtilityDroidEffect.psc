Scriptname ZP_UtilityDroidEffect extends ActiveMagicEffect
{Prophecy Gadgets - Utility Droid's ability (on the droid). Once a second it counts up two timers:
  - every HealInterval seconds, if the player is within HealRadius and hurt, it restores HealAmount Health to them;
  - every StaggerInterval seconds, while the droid is in combat, it casts StaggerSpell on each living actor hostile to
    the player within StaggerRadius of the droid (powerofthree's Papyrus Extender FindAllReferencesOfFormType, as
    Seismic Stomp does).
Stops when the droid dies.}

Spell Property StaggerSpell Auto
Spell Property HealSpell Auto              ; ZP_Prophecy_UtilityDroid_Heal: HealAmount through Enderal's heal-other effect, for its look
Float Property HealAmount = 15.0 Auto
Int Property HealInterval = 4 Auto
Float Property HealRadius = 640.0 Auto
Int Property StaggerInterval = 6 Auto
Float Property StaggerRadius = 300.0 Auto

Int Property kActorCharacter = 62 AutoReadOnly

Actor me
Int healTick
Int staggerTick

Event OnEffectStart(Actor akTarget, Actor akCaster)
	me = akTarget
	RegisterForSingleUpdate(1.0)
EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	me = None
EndEvent

Event OnUpdate()
	If !me || me.IsDead()
		Return
	EndIf
	Actor player = Game.GetPlayer()
	healTick += 1
	If healTick >= HealInterval
		healTick = 0
		If me.GetDistance(player) <= HealRadius && player.GetActorValuePercentage("Health") < 1.0
			Heal(player)
		EndIf
	EndIf
	staggerTick += 1
	If staggerTick >= StaggerInterval && me.IsInCombat()
		staggerTick = 0
		ObjectReference[] near = PO3_SKSEFunctions.FindAllReferencesOfFormType(me, kActorCharacter, StaggerRadius)
		Int i = 0
		While near && i < near.Length
			Actor a = near[i] as Actor
			If a && a != me && a != player && !a.IsDead() && a.IsHostileToActor(player)
				StaggerSpell.Cast(me, a)
			EndIf
			i += 1
		EndWhile
	EndIf
	RegisterForSingleUpdate(1.0)
EndEvent

Function Heal(Actor akPlayer)
	; the heal is a spell cast at the player (curator 2026-10-23: "an effect for when the droid heals me"): Enderal's
	; RestoreHealthFFActor shows its healing shimmer on them. A droid already out when this shipped has no HealSpell
	; (a property added to a running effect stays None in the save), so it is looked up, and the bare heal is the fallback.
	If !HealSpell
		HealSpell = Game.GetFormFromFile(0x0009AF, "Zenderal - Prophecy.esp") as Spell
	EndIf
	If HealSpell
		HealSpell.RemoteCast(me, me, akPlayer)
	Else
		akPlayer.RestoreActorValue("Health", HealAmount)
	EndIf
EndFunction
