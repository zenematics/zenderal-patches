Scriptname ZP_RighteousPathEffect extends ActiveMagicEffect
{Prophecy Faith - Righteous Path (Kittytails' Sunlight Targe as a passive, 2026-10-25). On the player's always-on ability.
While the player blocks with a spell or nothing in the left hand (so Dual Wield Parrying's spell-hand block counts, a
shield or left-hand weapon does not), each hit taken sends the Reflector Beam (CounterSpell) back at the attacker -
Kittytails' _LIP_SummonHolyShieldScript hit logic without its summoned shield: equipping that armor would push a spell
out of the left hand. The resistances and glow are condition-gated effects on the same ability.}

Spell Property CounterSpell Auto
Sound Property HitSFX Auto
Explosion Property ExplosionArtEffect Auto

Actor selfActor
Bool inSequence

Event OnEffectStart(Actor akTarget, Actor akCaster)
	selfActor = akTarget
EndEvent

; left hand: 0 = nothing, 9 = a spell
Bool Function WardUp()
	If !selfActor.GetAnimationVariableBool("IsBlocking")
		Return False
	EndIf
	Int left = selfActor.GetEquippedItemType(0)
	Return left == 0 || left == 9
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
