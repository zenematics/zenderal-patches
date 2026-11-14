Scriptname ZEN_PO_HighDexterityWardancerSC extends ActiveMagicEffect
{Vagrant: High Dexterity - Ordinator's Wardancer. While ZEN_PO_HighDexterityStruck is 0, the perk's entries give
+20% attack and critical damage (no heavy armor worn). An unblocked hit from a hostile actor sets it to 1 for
LockSeconds; a new hit restarts the timer. Lives on the ability the High Dexterity perk (069CFC) grants.}

GlobalVariable Property ZEN_PO_HighDexterityStruck Auto
Float Property LockSeconds = 6.0 Auto

Actor kOwner

Event OnEffectStart(Actor akTarget, Actor akCaster)
	kOwner = akTarget
	ZEN_PO_HighDexterityStruck.SetValue(0)
EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	ZEN_PO_HighDexterityStruck.SetValue(0)
EndEvent

Event OnHit(ObjectReference akAggressor, Form akSource, Projectile akProjectile, bool abPowerAttack, bool abSneakAttack, bool abBashAttack, bool abHitBlocked)
	If abHitBlocked
		Return
	EndIf
	Actor kAttacker = akAggressor as Actor
	If !kAttacker || kAttacker == kOwner || !kAttacker.IsHostileToActor(kOwner)
		Return
	EndIf
	ZEN_PO_HighDexterityStruck.SetValue(1)
	RegisterForSingleUpdate(LockSeconds)
EndEvent

Event OnUpdate()
	ZEN_PO_HighDexterityStruck.SetValue(0)
EndEvent
