Scriptname ZP_OwlAbsorbEffect extends ActiveMagicEffect
{Send an Owl's strike (Arcane Archery 4): the owl's own perk applies this as a combat-hit spell on everything it hits.
Drains up to Amount Magicka from the target and restores that much to the player (curator 2026-10-23). A plain Absorb
effect would give it to the owl, its caster, so the transfer is done here.}

Float Property Amount = 10.0 Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Float drained = akTarget.GetActorValue("Magicka")
	If drained > Amount
		drained = Amount
	EndIf
	If drained > 0.0
		akTarget.DamageActorValue("Magicka", drained)
		Game.GetPlayer().RestoreActorValue("Magicka", drained)
	EndIf
EndEvent
