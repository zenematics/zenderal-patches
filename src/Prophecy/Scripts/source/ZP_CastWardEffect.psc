Scriptname ZP_CastWardEffect extends ActiveMagicEffect
{Orbit Ward (Sorcery 2, 2026-10-28): an ability on the player, shaped like No Distractions (ZP_NoDistractionsEffect).
When the player starts casting a spell in either hand (the graph's BeginCastRight / BeginCastLeft) it casts the
talent's shield spell on the player - no Mana, Spell.Cast. Until 2026-11-14 that was Shatterveil's Orbit Ward, whose
DLL negated a whole hit per glass ward; now it is ZP_Prophecy_OrbitWard_Shield, and ZenProphecyRage.dll takes part of
each of the next few weapon hits while that effect is on (curator: block one or two hits, mitigate, never negate). While the ward is up the script polls the graph: once none of IsCastingRight, IsCastingLeft or
IsCastingDual is set for two polls in a row (the spell fired, the beam was let go, the cast was interrupted), it
dispels the ward. CastStop and Sheathe Begin (9) drop it at once. Only a ward this script cast is dispelled.
Animation-event registrations do not survive a game load, so they are renewed in OnPlayerLoadGame.
2026-11-14 (evLRise: "Orbit Ward ... triggers when you use a pistol, as it considers it a spell. It also triggers
while reloading"): a Flintlock pistol is a staff-type weapon, so its shot and its reload are casts to the graph
(BeginCastRight/Left, IsCastingRight/Left). A hand holding a staff-type weapon (type 8: pistols, staves) now neither
raises the ward nor counts as casting while it is up - only a hand with a spell in it does.}

Spell Property Shield Auto               ; ZP_Prophecy_OrbitWard_Shield (2026-11-14; was Ward = shvl_PrismWardSpell
                                         ; 000E55:Shatterveil.esp - renamed so a save's old value is not kept)
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
	ElseIf asEventName == "BeginCastLeft"
		If SpellHand(True)
			StartWard()
		EndIf
	ElseIf SpellHand(False)
		StartWard()
	EndIf
EndEvent

; True when that hand holds no staff-type weapon (pistols, staves): a cast from it is a spell cast.
Bool Function SpellHand(Bool left)
	Weapon w = player.GetEquippedWeapon(left)
	Return !w || w.GetWeaponType() != 8
EndFunction

Event OnActorAction(Int actionType, Actor akActor, Form source, Int slot)
	If akActor == player
		DropWard()
	EndIf
EndEvent

Function StartWard()
	RegisterCast()          ; cheap; covers a save loaded without OnPlayerLoadGame reaching this effect
	If !ours
		Shield.Cast(player, player)
		ours = True
	EndIf
	misses = 0
	RegisterForSingleUpdate(PollSeconds)
EndFunction

Bool Function Casting()
	If player.GetAnimationVariableBool("IsCastingRight") && SpellHand(False)
		Return True
	EndIf
	If player.GetAnimationVariableBool("IsCastingLeft") && SpellHand(True)
		Return True
	EndIf
	Return player.GetAnimationVariableBool("IsCastingDual") && SpellHand(False) && SpellHand(True)
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
		player.DispelSpell(Shield)
	EndIf
EndFunction
