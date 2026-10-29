Scriptname ZP_CastWardEffect extends ActiveMagicEffect
{Orbit Ward (Sorcery 2, 2026-10-28): an ability on the player, shaped like No Distractions (ZP_NoDistractionsEffect).
When the player starts casting a spell in either hand (the graph's BeginCastRight / BeginCastLeft) it casts
Shatterveil's Orbit Ward on the player - no Mana, Spell.Cast - and Shatterveil's DLL raises the orbiting wards on that
effect's apply event. While the ward is up the script polls the graph: once none of IsCastingRight, IsCastingLeft or
IsCastingDual is set for two polls in a row (the spell fired, the beam was let go, the cast was interrupted), it
dispels the ward. CastStop and Sheathe Begin (9) drop it at once. Only a ward this script cast is dispelled.
Animation-event registrations do not survive a game load, so they are renewed in OnPlayerLoadGame.}

Spell Property Ward Auto                 ; shvl_PrismWardSpell 000E55:Shatterveil.esp
Float Property PollSeconds = 0.25 Auto

Actor player
Bool ours
Int misses

Event OnEffectStart(Actor akTarget, Actor akCaster)
	player = akTarget
	RegisterForActorAction(9)
	RegisterCast()
EndEvent

Event OnPlayerLoadGame()
	RegisterCast()
EndEvent

Function RegisterCast()
	RegisterForAnimationEvent(player, "BeginCastRight")
	RegisterForAnimationEvent(player, "BeginCastLeft")
	RegisterForAnimationEvent(player, "CastStop")
EndFunction

Event OnAnimationEvent(ObjectReference akSource, String asEventName)
	If akSource != player
		Return
	EndIf
	If asEventName == "CastStop"
		DropWard()
	Else
		StartWard()
	EndIf
EndEvent

Event OnActorAction(Int actionType, Actor akActor, Form source, Int slot)
	If akActor == player
		DropWard()
	EndIf
EndEvent

Function StartWard()
	RegisterCast()          ; cheap; covers a save loaded without OnPlayerLoadGame reaching this effect
	If !ours
		Ward.Cast(player, player)
		ours = True
	EndIf
	misses = 0
	RegisterForSingleUpdate(PollSeconds)
EndFunction

Bool Function Casting()
	Return player.GetAnimationVariableBool("IsCastingRight") || player.GetAnimationVariableBool("IsCastingLeft") || player.GetAnimationVariableBool("IsCastingDual")
EndFunction

Event OnUpdate()
	If !ours
		Return
	EndIf
	If Casting()
		misses = 0
	Else
		misses += 1
		If misses >= 2
			DropWard()
			Return
		EndIf
	EndIf
	RegisterForSingleUpdate(PollSeconds)
EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	DropWard()
EndEvent

Function DropWard()
	If ours
		ours = False
		player.DispelSpell(Ward)
	EndIf
EndFunction
