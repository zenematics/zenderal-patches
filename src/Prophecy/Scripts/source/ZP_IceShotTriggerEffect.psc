Scriptname ZP_IceShotTriggerEffect extends ActiveMagicEffect
{Ice Shot's hit: a 1 s effect on the shared gun hit spell (bow hits, Ice Shot perk). If an ice arrow was fired within
Window (ZP_IceShotWatcherEffect's LastShot/Pending) and the target is not already frozen, it casts Freeze (25 frost +
ZP_IceShotFreezeEffect for 8 s) straight onto the target. This replaced the ice arrow's explosion enchantment as the
delivery (2026-10-23): a 100-unit explosion missed big creatures such as bears. A frozen target is left alone - that
hit is the shatter, which the freeze effect's own OnHit handles.}

Spell Property Freeze Auto
MagicEffect Property FreezeEffect Auto
GlobalVariable Property LastShot Auto
GlobalVariable Property Pending Auto
Float Property Window = 3.0 Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	If !akCaster || akTarget.IsDead() || akTarget.IsPlayerTeammate()
		Return
	EndIf
	Float now = Utility.GetCurrentRealTime()
	Float last = LastShot.GetValue()
	Debug.Trace("ZP_IceShot hit on " + akTarget + " at " + now + ": pending " + Pending.GetValue() + ", last ice shot " + last + ", frozen " + akTarget.HasMagicEffect(FreezeEffect))
	If Pending.GetValue() < 1 || now < last || now - last > Window
		Return                                  ; not an ice arrow
	EndIf
	Pending.SetValue(Pending.GetValue() - 1)
	If akTarget.HasMagicEffect(FreezeEffect)
		Return                                  ; already frozen: this hit shatters it
	EndIf
	Freeze.Cast(akCaster, akTarget)
EndEvent
