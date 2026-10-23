Scriptname ZP_SeismicStompEffect extends ActiveMagicEffect
{Prophecy Glory - Seismic Stomp (lesser power). Enderal's own stomp beat (_00E_MQ15_Functions.TealorBreakWall):
play the stomp idle, wait for the foot to land, set off the shockwave and shake the camera. Then every hostile living
actor within Radius is thrown back and up and starts to bleed (Bleeding Shot's bleed, 10/s for 5 s), while time slows
(SlowTime spell: world at 30% for 10 s; the player keeps full speed - see the perk).
The launch: PushActorAway ragdolls them away from the player, then - once the ragdoll exists - an upward havok impulse
lifts them (aimed at about 3 feet; LiftImpulse is the knob, as Frozen Electrocuted Combustion lifts ragdolls).
The 30 s cooldown is the Cooldown spell's effect on the player (Templar's pattern): while it lasts the power does
nothing but say so. Needs powerofthree's Papyrus Extender (FindAllReferencesOfFormType).
Which animation (2026-10-22): Enderal's stomp (_00E_IdleStomp, FNIS) is an UNARMED idle - played with a weapon out it
left the graph unarmed while the sword stayed in hand, and no attack worked. So:
  * melee weapon or fists out: Hot Key Skill's CustomStartJ event (an unconditioned transition in 1hm_behavior that
    plays HKS_CustomAnimJ.hkx and returns to the drawn weapon by itself). tools/04 puts Enderal's stomp.hkx into that
    slot through an OAR submod;
  * weapons away: the Enderal idle as before, then IdleForceDefaultState (how Enderal ends its idles);
  * bow, crossbow, staff or spell out: no animation, so nothing can desync.}

Idle Property StompIdle Auto
Explosion Property Shockwave Auto
Spell Property Bleed Auto
Spell Property SlowTime Auto
Spell Property Cooldown Auto
MagicEffect Property CooldownEffect Auto
Float Property Radius = 400.0 Auto
Float Property KnockForce = 4.0 Auto
Float Property LiftImpulse = 150.0 Auto   ; 2026-10-22: 200 flew too high; height grows with the square, 150 ~ 56%
Float Property ImpactDelay = 0.5 Auto
Float Property RecoverDelay = 0.8 Auto   ; after the impact, let the stomp finish before freeing the player

Int Property kActorCharacter = 62 AutoReadOnly

Event OnEffectStart(Actor akTarget, Actor akCaster)
	If akCaster.HasMagicEffect(CooldownEffect)
		Debug.Notification("Seismic Stomp is not ready yet.")
		Return
	EndIf
	Cooldown.Cast(akCaster, akCaster)
	Bool idlePlayed = False
	If akCaster.IsWeaponDrawn()
		If akCaster.GetEquippedItemType(1) <= 6            ; fists (0) .. two-handed axe/hammer (6): the melee graph
			Debug.SendAnimationEvent(akCaster, "CustomStartJ")
		EndIf
	Else
		akCaster.PlayIdle(StompIdle)
		idlePlayed = True
	EndIf
	Utility.Wait(ImpactDelay)
	akCaster.PlaceAtMe(Shockwave)
	Game.ShakeCamera(None, 0.5)

	ObjectReference[] near = PO3_SKSEFunctions.FindAllReferencesOfFormType(akCaster, kActorCharacter, Radius)
	Actor[] hit = new Actor[32]
	Int n = 0
	Int i = 0
	While near && i < near.Length && n < hit.Length
		Actor a = near[i] as Actor
		If a && a != akCaster && !a.IsDead() && a.IsHostileToActor(akCaster)
			akCaster.PushActorAway(a, KnockForce)
			hit[n] = a
			n += 1
		EndIf
		i += 1
	EndWhile
	If n > 0
		SlowTime.Cast(akCaster, akCaster)
		Utility.Wait(0.1)      ; PushActorAway's ragdoll must exist before the impulse can lift it
		i = 0
		While i < n
			hit[i].ApplyHavokImpulse(0.0, 0.0, 1.0, LiftImpulse)
			Bleed.Cast(akCaster, hit[i])
			i += 1
		EndWhile
	EndIf
	If idlePlayed
		Utility.Wait(RecoverDelay)
		Debug.SendAnimationEvent(akCaster, "IdleForceDefaultState")
	EndIf
EndEvent
