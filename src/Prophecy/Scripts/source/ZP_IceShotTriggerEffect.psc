Scriptname ZP_IceShotTriggerEffect extends ActiveMagicEffect
{Ice Shot's hit: a 1 s effect on the shared gun hit spell (bow hits, Ice Shot perk). If an ice arrow was fired within
Window (ZP_IceShotWatcherEffect's LastShot/Pending) and the target is not already frozen, it casts Freeze (25 frost +
ZP_IceShotFreezeEffect for 8 s) straight onto the target. This replaced the ice arrow's explosion enchantment as the
delivery (2026-10-23): a 100-unit explosion missed big creatures such as bears. A frozen target is left alone - that
hit is the shatter, which the freeze effect's own OnHit handles.
2026-10-28: an arrow that hits an actor goes into its inventory, so ice arrows were lootable from enemies. Every bow
hit now takes them back off the target (also dead ones), at once and again after StripDelay, as the engine adds the
arrow around the hit. Not done by making the ammo non-playable: the power equips it on the player.}

Spell Property Freeze Auto
MagicEffect Property FreezeEffect Auto
GlobalVariable Property LastShot Auto
GlobalVariable Property Pending Auto
Ammo Property IceArrow Auto
Float Property Window = 3.0 Auto
Float Property StripDelay = 0.5 Auto

Function StripIceArrows(Actor akTarget)
	If IceArrow && akTarget
		Int n = akTarget.GetItemCount(IceArrow)
		If n > 0
			akTarget.RemoveItem(IceArrow, n, True)
		EndIf
	EndIf
EndFunction

Event OnEffectStart(Actor akTarget, Actor akCaster)
	StripIceArrows(akTarget)
	RegisterForSingleUpdate(StripDelay)
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

Event OnUpdate()
	StripIceArrows(GetTargetActor())
EndEvent
