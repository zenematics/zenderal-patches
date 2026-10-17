Scriptname _00E_A1_FireArrowSC extends activemagiceffect

Import _00E_TalentLibrary

;=====================================================================================
;              							EVENTS
;=====================================================================================

Event OnUpdate()

	PlayerRef.UnequipItem(amShotAmmo, GetArrowCount())
	Self.Dispel()

EndEvent

Event OnEffectStart(Actor akTarget, Actor akCaster)

	iIndex = GetPlayerTalentLevel(_00E_Class_Trickery_P05_Talent_Firearrow, _00E_Class_Trickery_P05_Talent_Firearrow2, _00E_Class_Trickery_P05_Talent_Firearrow3)
	AdjustArrowEnchantment()
	; ZP: a crossbow-type weapon (Ordo's muskets) cannot fire arrows - hand out flame musket balls instead.
	; They explode with the fire arrow's own explosion, so the enchantment set above applies to them too.
	amShotAmmo = _00E_A1_FireArrowAmm
	If ZP_FlameShotMusketBall && PlayerREF.GetEquippedItemType(1) == 12
		amShotAmmo = ZP_FlameShotMusketBall
	EndIf
	amOldAmmo = GetEquippedAmmo()
	akCaster.AddItem(amShotAmmo, GetArrowCount())
	akcaster.EquipItem(amShotAmmo)
	AddInventoryEventFilter(amShotAmmo)

EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)

	If PlayerREF.GetItemCount(amShotAmmo) > 0
		PlayerREF.UnequipItem(amShotAmmo)
		PlayerREF.RemoveItem(amShotAmmo, GetArrowCount())
	EndIf

	; ZP: only re-equip ammo that was found; SureAI's version equipped None when the old ammo was unknown.
	If amOldAmmo
		PlayerREF.EquipItem(amOldAmmo)
	EndIf

EndEvent

Event OnPlayerBowShot(Weapon akWeapon, Ammo akAmmo, float afPower, bool abSunGazing)

	If (akAmmo == amShotAmmo)
		_00E_A1_FireArrowIgniteSound.Play(PlayerREF)
	EndIf

	counter += 1

	If(counter == GetArrowCount()) && PlayerREF.GetItemCount(amShotAmmo) == 0
		RegisterForSingleUpdate(2)
	EndIf

EndEvent

Event OnItemRemoved(Form akBaseItem, int aiItemCount, ObjectReference akItemReference, ObjectReference akDestContainer)
	If akItemReference && ! akDestContainer
		akItemReference.Delete()
	EndIf
EndEvent

;=====================================================================================
;              							FUNCTION
;=====================================================================================

Ammo Function GetEquippedAmmo()

	bool bFound
	int iFormlistIndex = _00E_A1_FirearrowAmmoFormlist.GetSize() - 1

	While iFormlistIndex >= 0 && !bFound

		Ammo amCurrentAmmoEntry = _00E_A1_FirearrowAmmoFormlist.GetAt(iFormlistIndex) as Ammo

		if PlayerREF.IsEquipped(amCurrentAmmoEntry)
			bFound = True
			Return amCurrentAmmoEntry
		Else
			iFormlistIndex -= 1
		EndIf

	EndWhile

EndFunction

Function AdjustArrowEnchantment()

	float iArrowFireDamage = _00E_A1_FireArrowSP.GetNthEffectMagnitude(iIndex - 1)

	_00E_A1_FireArrowEnchantment.SetNthEffectMagnitude(1, iArrowFireDamage)

	If PlayerREF.HasSpell(_00E_Affinity_AbWayfarer)
		_00E_A1_FireArrowWayfarerEnch.SetNthEffectMagnitude(0, (_00E_A1_FireArrowSP.GetNthEffectMagnitude(6)))
	EndIf

EndFunction

int Function GetArrowCount()

	int iArrowCount = _00E_A1_FireArrowSP.GetNthEffectMagnitude(iIndex + 2) as Int

	Return iArrowCount

EndFunction

;=====================================================================================
;              							PROPERTIES
;=====================================================================================

Ammo amOldAmmo
Ammo amShotAmmo ; ZP: the fire arrow or the flame musket ball handed out by this cast

int iIndex
int Counter

Formlist Property _00E_A1_FirearrowAmmoFormlist Auto

Enchantment Property _00E_A1_FireArrowEnchantment Auto
Enchantment Property _00E_A1_FireArrowWayfarerEnch Auto

Ammo Property _00E_A1_FireArrowAmm Auto
Ammo Property ZP_FlameShotMusketBall Auto ; ZP: filled by Zenderal - Flame Shot.esp's override of 05BD36

Perk Property _00E_Class_Trickery_P05_Talent_Firearrow Auto
Perk Property _00E_Class_Trickery_P05_Talent_Firearrow2 Auto
Perk Property _00E_Class_Trickery_P05_Talent_Firearrow3 Auto
Spell Property _00E_Affinity_AbWayfarer Auto

Actor Property PlayerREF Auto

Sound property _00E_A1_FireArrowIgniteSound Auto

Spell Property _00E_A1_FireArrowSP Auto
