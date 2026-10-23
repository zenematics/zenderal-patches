Scriptname ZP_SecondWindEffect extends ActiveMagicEffect
{Prophecy Glory - Second Wind (ability): while the player is at or below HealthThreshold of their Health, every hit
they take restores Stamina. Combat frameworks report one weapon hit as several OnHit events (the weapon plus their hit
spells - arch-docs/patches/BrawlFixes.md), so hits closer together than 0.25 s count once.}

Float Property Stamina = 20.0 Auto
Float Property HealthThreshold = 0.5 Auto

Float lastHit

Event OnHit(ObjectReference akAggressor, Form akSource, Projectile akProjectile, Bool abPowerAttack, Bool abSneakAttack, Bool abBashAttack, Bool abHitBlocked)
	Actor me = GetTargetActor()
	If !akAggressor || akAggressor == me
		Return
	EndIf
	If me.GetActorValuePercentage("Health") > HealthThreshold
		Return
	EndIf
	Float now = Utility.GetCurrentRealTime()
	If now - lastHit < 0.25 && now >= lastHit
		Return
	EndIf
	lastHit = now
	me.RestoreActorValue("Stamina", Stamina)
EndEvent
