Scriptname ZP_DarkEffigyEffect extends ActiveMagicEffect
{Prophecy Necromancy - Dark Effigy (a spell, effect lasts Duration on the player). Plants a dark totem in front of the
player (a hagraven's goat pole, War Banner's placing pattern) with an eldritch puff. Once a second, while the effect
lasts, for every living actor within Radius of the totem:
  - each ally (the player, a teammate, a summon or raised corpse the player commands, a Legion of the Damned skeleton)
    gets ArmorSpell (+250 armor for 2 s, so it fades soon after leaving the totem);
  - each of those that is undead (ActorTypeUndead, or a raised corpse: its reanimate effect carries MagicSummonUndead)
    and is the player's own (commanded or Legion) also heals HealPerSecond.
Casting it again replaces the totem (the old effect ends and takes its totem with it).
Needs powerofthree's Papyrus Extender (FindAllReferencesOfFormType, GetCommandingActor).}

Static Property Totem Auto                ; HagravenDeadGoatPole01
Explosion Property PlantVisual Auto       ; Willing Sacrifice's eldritch puff, no damage
Spell Property ArmorSpell Auto
Keyword Property ActorTypeUndead Auto
Keyword Property MagicSummonUndead Auto
FormList Property LegionList Auto
Float Property Radius = 512.0 Auto
Float Property HealPerSecond = 2.0 Auto
Float Property PlantDistance = 150.0 Auto
Float Property TotemScale = 1.4 Auto

Int Property kActorCharacter = 62 AutoReadOnly

Actor player
ObjectReference totemRef
Bool finished

Event OnEffectStart(Actor akTarget, Actor akCaster)
	player = akCaster
	Form xmarker = Game.GetForm(0x34)                      ; XMarker 000034:Skyrim.esm
	Float a = player.GetAngleZ()
	ObjectReference spot = player.PlaceAtMe(xmarker)
	spot.MoveTo(player, PlantDistance * Math.Sin(a), PlantDistance * Math.Cos(a), 0.0, False)
	spot.SetAngle(0.0, 0.0, a + 180.0)                     ; facing the player
	totemRef = spot.PlaceAtMe(Totem)
	totemRef.SetScale(TotemScale)
	spot.PlaceAtMe(PlantVisual)
	spot.Delete()
	If finished
		Cleanup()
		Return
	EndIf
	RegisterForSingleUpdate(0.1)
EndEvent

Event OnUpdate()
	If !totemRef || finished
		Return
	EndIf
	ObjectReference[] near = PO3_SKSEFunctions.FindAllReferencesOfFormType(totemRef, kActorCharacter, Radius)
	Int i = 0
	While near && i < near.Length
		Actor a = near[i] as Actor
		If a && !a.IsDead()
			Bool own = PO3_SKSEFunctions.GetCommandingActor(a) == player || LegionList.HasForm(a)
			If a == player || own || a.IsPlayerTeammate()
				ArmorSpell.RemoteCast(player, player, a)
				If own && (a.HasKeyword(ActorTypeUndead) || a.HasEffectKeyword(MagicSummonUndead))
					a.RestoreActorValue("Health", HealPerSecond)
				EndIf
			EndIf
		EndIf
		i += 1
	EndWhile
	RegisterForSingleUpdate(1.0)
EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	finished = True                       ; OnUpdate stops on it (UnregisterForUpdate here only errors: the effect is gone)
	Cleanup()
EndEvent

Function Cleanup()
	If totemRef
		totemRef.Disable(True)
		totemRef.Delete()
		totemRef = None
	EndIf
EndFunction
