Scriptname ZP_NoDistractionsEffect extends ActiveMagicEffect
{No Distractions (Arcane Archery 2): an ability on the player. When a bow (only - item type 7, not crossbows or Ordo's
muskets) starts drawing it casts Spell Ward (Rank II) on the player - in this list that is Levin's Enderal Spell Ward
Rework's fire-and-forget shell ward (sphere, start/hit/end explosions). The draw start is the behavior graph's
bowAttackStart / BowDraw / bowDrawStart events (whichever comes first); SKSE's Bow Draw action (5) only fires once the
bow is fully drawn (curator, in game 2026-10-23) and is kept as a fallback. While the ward is up the script polls the
graph: once neither IsAttacking nor bBowDrawn is set (fired, lowered the bow without firing, sheathed) for two polls in
a row, it dispels the ward. Bow Release (6) and Sheathe Begin (9) drop it at once. Only a ward this script cast is
ever dispelled - a ward the player cast stays. Animation-event registrations do not survive a game load, so they are
renewed in OnPlayerLoadGame.}

Spell Property Ward Auto                 ; _10E_SpellSpellWard 085654 (Spell Ward, Rank II)
Keyword Property MagicWard Auto          ; any ward effect already on the player
Float Property PollSeconds = 0.25 Auto

Actor player
Bool ours
Int misses

Event OnEffectStart(Actor akTarget, Actor akCaster)
	player = akTarget
	RegisterForActorAction(5)
	RegisterForActorAction(6)
	RegisterForActorAction(9)
	RegisterDrawStart()
EndEvent

Event OnPlayerLoadGame()
	RegisterDrawStart()
EndEvent

Function RegisterDrawStart()
	RegisterForAnimationEvent(player, "bowAttackStart")
	RegisterForAnimationEvent(player, "BowDraw")
	RegisterForAnimationEvent(player, "bowDrawStart")
EndFunction

Event OnAnimationEvent(ObjectReference akSource, String asEventName)
	If akSource == player
		StartWard()
	EndIf
EndEvent

Event OnActorAction(Int actionType, Actor akActor, Form source, Int slot)
	If akActor != player
		Return
	EndIf
	If actionType == 5
		StartWard()
	Else
		DropWard()
	EndIf
EndEvent

Function StartWard()
	RegisterDrawStart()     ; cheap; covers a save loaded without OnPlayerLoadGame reaching this effect
	If player.GetEquippedItemType(1) != 7
		Return
	EndIf
	If !ours && !player.HasMagicEffectWithKeyword(MagicWard)
		Ward.Cast(player, player)
		ours = True
	EndIf
	misses = 0
	RegisterForSingleUpdate(PollSeconds)
EndFunction

Event OnUpdate()
	If !ours
		Return
	EndIf
	If player.GetAnimationVariableBool("IsAttacking") || player.GetAnimationVariableBool("bBowDrawn")
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
