Scriptname ZP_DrowningOrbWatch extends ActiveMagicEffect
{Prophecy Sorcery - Drowning Orb (2026-10-27). The orb is Obscure Magic's hazard, which never applies its spell to its
own caster (a Mana restore added to that spell did nothing for the player in game). This ability, given by the
Drowning Orb talent, waits for the player to cast the orb spell; for WatchSeconds after it, while the player is within
Radius of an orb hazard, it restores RestorePerSecond Mana per second.}

Spell Property OrbSpell Auto              ; _K01_PsijicWaterGlobe, "Drowning Orb"
Form Property OrbHazard Auto              ; _K01_PsijicWaterGlobeHazard
Float Property Radius = 320.0 Auto        ; the mesh's BlastRadiusNode; the bubble itself is ~200
Float Property RestorePerSecond = 10.0 Auto
Float Property WatchSeconds = 12.0 Auto   ; the hazard's 10 s lifetime + the projectile's flight
Float Property Tick = 0.5 Auto

Actor player
Float watchUntil = 0.0
Bool found = False

Event OnEffectStart(Actor akTarget, Actor akCaster)
	player = akTarget
EndEvent

Event OnSpellCast(Form akSpell)
	If akSpell != OrbSpell || !player
		Return
	EndIf
	Bool wasIdle = watchUntil < Utility.GetCurrentRealTime()
	watchUntil = Utility.GetCurrentRealTime() + WatchSeconds
	If wasIdle
		found = False
		RegisterForSingleUpdate(Tick)
	EndIf
EndEvent

Event OnUpdate()
	If !player
		Return
	EndIf
	ObjectReference orb = Game.FindClosestReferenceOfTypeFromRef(OrbHazard, player, Radius)
	If orb
		found = True
		player.RestoreActorValue("Magicka", RestorePerSecond * Tick)
	EndIf
	If Utility.GetCurrentRealTime() < watchUntil
		RegisterForSingleUpdate(Tick)
	ElseIf !found
		Debug.Trace("ZP_DrowningOrbWatch: no Drowning Orb hazard within " + Radius + " of the player during the watch")
	EndIf
EndEvent
