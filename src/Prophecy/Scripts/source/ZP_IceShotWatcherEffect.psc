Scriptname ZP_IceShotWatcherEffect extends ActiveMagicEffect
{Ice Shot's watcher: an ability on the player from the Ice Shot perk (always on, so nothing depends on the power's
short-lived effect). Every ice arrow fired (OnPlayerBowShot, SureAI's Flame Shot event) is recorded for
ZP_IceShotTriggerEffect: LastShot = real time, Pending += 1 (reset when the last one is older than Window). It also
counts the cast's shots down (Remaining, set by the power): at zero the ice arrows are done - any still in the
inventory are taken (in game 2026-10-23 fired arrows were sometimes put back, so the count never reached zero) and the
remembered ammo (OldAmmo) goes back on.}

Ammo Property IceArrow Auto
FormList Property OldAmmo Auto
GlobalVariable Property LastShot Auto        ; Utility.GetCurrentRealTime() of the last ice arrow fired
GlobalVariable Property Pending Auto         ; ice arrows fired within Window that have not frozen anything yet
GlobalVariable Property Remaining Auto       ; ice shots left from the last cast
Float Property Window = 3.0 Auto
Float Property RestoreDelay = 1.0 Auto

Actor player

Event OnEffectStart(Actor akTarget, Actor akCaster)
	player = akTarget
EndEvent

Event OnPlayerBowShot(Weapon akWeapon, Ammo akAmmo, Float afPower, Bool abSunGazing)
	If akAmmo != IceArrow
		Return
	EndIf
	Float now = Utility.GetCurrentRealTime()
	Float last = LastShot.GetValue()
	If now - last > Window || now < last
		Pending.SetValue(0)
	EndIf
	LastShot.SetValue(now)
	Pending.SetValue(Pending.GetValue() + 1)
	FillRemaining()
	Remaining.SetValue(Remaining.GetValue() - 1)
	Debug.Trace("ZP_IceShot watcher: ice arrow fired at " + now + ", pending " + Pending.GetValue() + ", shots left " + Remaining.GetValue() + ", held " + player.GetItemCount(IceArrow))
	If Remaining.GetValue() <= 0 || player.GetItemCount(IceArrow) == 0
		RegisterForSingleUpdate(RestoreDelay)
	EndIf
EndEvent

; A property added to this script after a save's watcher started stays None in that running instance (in game
; 2026-10-23: Remaining read as 0, so the first ice shot "ended" the cast). Look the global up by its FormID then.
Function FillRemaining()
	If !Remaining
		Remaining = Game.GetFormFromFile(0x000991, "Zenderal - Prophecy.esp") as GlobalVariable
	EndIf
EndFunction

Event OnUpdate()
	Int held = player.GetItemCount(IceArrow)
	If held > 0
		player.UnequipItem(IceArrow, False, True)
		player.RemoveItem(IceArrow, held, True)
	EndIf
	FillRemaining()
	Remaining.SetValue(0)
	If OldAmmo.GetSize() == 0
		Return
	EndIf
	Ammo old = OldAmmo.GetAt(0) as Ammo
	OldAmmo.Revert()
	If old && player.GetItemCount(old) > 0
		player.EquipItem(old, False, True)
	EndIf
EndEvent
