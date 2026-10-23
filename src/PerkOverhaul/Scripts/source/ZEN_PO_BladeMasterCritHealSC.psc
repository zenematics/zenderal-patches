Scriptname ZEN_PO_BladeMasterCritHealSC extends ActiveMagicEffect
{Blade Dancer: Blade Master - a critical hit with a one-handed sword or dagger restores HealAmount Health.
Lives on the ability the Blade Master perk (069D52) grants. Needs powerofthree's Papyrus Extender (OnCriticalHit).}

Keyword Property WeapTypeSword Auto
Keyword Property WeapTypeDagger Auto
Float Property HealAmount = 10.0 Auto

Actor kOwner

Event OnEffectStart(Actor akTarget, Actor akCaster)
	kOwner = akTarget
	PO3_Events_AME.RegisterForCriticalHit(Self)
EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	PO3_Events_AME.UnregisterForCriticalHit(Self)
EndEvent

Event OnCriticalHit(Actor akAggressor, Weapon akWeapon, bool abSneakHit)
	If akAggressor != kOwner || !akWeapon
		Return
	EndIf
	If akWeapon.HasKeyword(WeapTypeSword) || akWeapon.HasKeyword(WeapTypeDagger)
		akAggressor.RestoreActorValue("Health", HealAmount)
	EndIf
EndEvent
