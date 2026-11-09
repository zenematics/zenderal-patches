Scriptname ZP_CastOnTargetEffect extends ActiveMagicEffect
{Prophecy - a relay: casts SpellToCast from the caster at the target once, when this effect is applied.
Bleeding Shot's musket bleed (2026-11-08, GreaseLord: "if you switch to another weapon the bleeding will stop ...
only happens to muskets"): the gun hit spell's effects are conditioned on the musket in the player's hand (the spell
is shared with the bow talents), and the engine re-checks an active effect's conditions while it runs, so the 5 s
bleed ended the moment the player switched weapons, and dealt less than its 50. This relay lasts a second, so its
conditions are read once at the hit; the bleed it casts (Seismic Stomp's bleed spell, the one the pistol branch uses)
carries no condition and runs its full 5 s whatever the player holds.}

Spell Property SpellToCast Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	If SpellToCast && akTarget && akCaster && !akTarget.IsDead()
		SpellToCast.Cast(akCaster, akTarget)
	EndIf
EndEvent
