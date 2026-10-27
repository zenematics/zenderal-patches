Scriptname ZP_RighteousPathEffect extends ActiveMagicEffect
{Prophecy Faith - Righteous Path (Kittytails' Sunlight Targe as a passive, 2026-10-25). On the player's always-on ability.
While the player blocks with a spell or nothing in the left hand (so Dual Wield Parrying's spell-hand block counts, a
shield or left-hand weapon does not):
- the ward shows: WardShield, Kittytails' shield of light copied into the FX01 slot, is worn (her own shield goes in the
  shield slot, which would push a spell out of the left hand). Put on at the block's start, checked every 0.25 s while
  up, taken off when the block ends or the conditions stop holding;
- each hit taken sends the Reflector Beam (CounterSpell) back at the attacker - Kittytails' hit logic - for 10 Mana
  (2026-10-26); with less than 10 Mana the block is an ordinary block.
The resistances are condition-gated effects on the same ability.}

Spell Property CounterSpell Auto
Sound Property HitSFX Auto
Explosion Property ExplosionArtEffect Auto
Armor Property WardShield Auto

Actor selfActor
Bool inSequence
Bool wardShown

Event OnEffectStart(Actor akTarget, Actor akCaster)
	selfActor = akTarget
	RegisterForAnimationEvent(selfActor, "blockStart")
	RegisterForAnimationEvent(selfActor, "blockStartOut")
	RegisterForAnimationEvent(selfActor, "blockStop")
	RegisterForAnimationEvent(selfActor, "blockStopOut")
	UpdateWard()
EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	HideWard()
EndEvent

; left hand: 0 = nothing, 9 = a spell
Bool Function WardUp()
	If !selfActor || !selfActor.GetAnimationVariableBool("IsBlocking")
		Return False
	EndIf
	Int left = selfActor.GetEquippedItemType(0)
	Return left == 0 || left == 9
EndFunction

Event OnAnimationEvent(ObjectReference akSource, String asEventName)
	If asEventName == "blockStart" || asEventName == "blockStartOut"
		Utility.Wait(0.05)    ; IsBlocking is set as the block state is entered
	EndIf
	UpdateWard()
EndEvent

Event OnUpdate()
	UpdateWard()
EndEvent

Function UpdateWard()
	If SKSE.GetPluginVersion("ZenProphecyUI") > 0    ; Prophecy v3's DLL shows and hides the ward itself, at once
		Return
	EndIf
	If WardUp()
		If !wardShown
			ShowWard()
		EndIf
		RegisterForSingleUpdate(0.25)
	ElseIf wardShown
		HideWard()
	EndIf
EndFunction

Function ShowWard()
	If !WardShield    ; an instance saved before the property existed keeps it None
		WardShield = Game.GetFormFromFile(0xA68, "Zenderal - Prophecy.esp") as Armor   ; ZP_Prophecy_RighteousPath_Ward
	EndIf
	If !WardShield || !selfActor
		Return
	EndIf
	wardShown = True
	If selfActor.GetItemCount(WardShield) < 1
		selfActor.AddItem(WardShield, 1, True)
	EndIf
	selfActor.EquipItem(WardShield, True, True)
EndFunction

Function HideWard()
	wardShown = False
	If WardShield && selfActor && selfActor.GetItemCount(WardShield) > 0
		selfActor.UnequipItem(WardShield, True, True)
		selfActor.RemoveItem(WardShield, selfActor.GetItemCount(WardShield), True)
	EndIf
EndFunction

Event OnHit(ObjectReference akAggressor, Form akSource, Projectile akProjectile, Bool abPowerAttack, Bool abSneakAttack, Bool abBashAttack, Bool abHitBlocked)
	If inSequence || !selfActor || akAggressor == selfActor || !(akAggressor as Actor) || !WardUp()
		Return
	EndIf
	; as Kittytails': a blocked hit, or a spell or arrow coming from the front while blocking
	Bool frontal = Math.Abs(selfActor.GetHeadingAngle(akAggressor)) < 60.0
	If !abHitBlocked && !(frontal && ((akSource as Spell) || (akSource as Weapon && (akSource as Weapon).IsBow())))
		Return
	EndIf
	; the beam costs 10 Mana (curator 2026-10-26); without it the block is just a block. A literal, not a property:
	; a property added later stays unset in saves that already run this effect
	Float beamMana = 10.0
	If selfActor.GetActorValue("Magicka") < beamMana
		Return
	EndIf
	selfActor.DamageActorValue("Magicka", beamMana)
	If !abHitBlocked
		selfActor.ClearExtraArrows()
	EndIf
	inSequence = True
	HitSFX.Play(selfActor)
	selfActor.PlaceAtMe(ExplosionArtEffect)
	CounterSpell.Cast(selfActor, akAggressor)
	Utility.Wait(0.25)
	inSequence = False
EndEvent
