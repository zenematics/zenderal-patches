Scriptname ZP_SurroundedEffect extends ActiveMagicEffect
{Prophecy Glory - Surrounded (ability, perk 0x93A - Death or Glory's slot): once a second, while the player is in
combat, counts the living actors hostile to them within Radius; at MinEnemies or more it restores StaminaPerSecond
Stamina. Uses Seismic Stomp's search (powerofthree's Papyrus Extender FindAllReferencesOfFormType) and stops counting
as soon as the threshold is met.}

Float Property Radius = 400.0 Auto
Int Property MinEnemies = 3 Auto
Float Property StaminaPerSecond = 2.0 Auto

Int Property kActorCharacter = 62 AutoReadOnly

Actor me

Event OnEffectStart(Actor akTarget, Actor akCaster)
	me = akTarget
	RegisterForSingleUpdate(1.0)
EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	me = None
EndEvent

Event OnUpdate()
	If !me
		Return
	EndIf
	If me.IsInCombat() && CountEnemies() >= MinEnemies
		me.RestoreActorValue("Stamina", StaminaPerSecond)
	EndIf
	RegisterForSingleUpdate(1.0)
EndEvent

Int Function CountEnemies()
	ObjectReference[] near = PO3_SKSEFunctions.FindAllReferencesOfFormType(me, kActorCharacter, Radius)
	Int n = 0
	Int i = 0
	While near && i < near.Length && n < MinEnemies
		Actor a = near[i] as Actor
		If a && a != me && !a.IsDead() && a.IsHostileToActor(me)
			n += 1
		EndIf
		i += 1
	EndWhile
	Return n
EndFunction
