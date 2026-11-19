Scriptname ZP_CalderaEquipScript extends ObjectReference
{Caldera (Zenderal), on the hammer: equipping it gives the player the tier ability (ZP_CalderaTiersScript, which shows
the charge in the head's cracks); unequipping takes it away once the hammer is no longer in hand (checked after a
moment: a swap between two copies equips the new one first or last). The charges themselves stay (Charges) and show
again on the next equip. Argent Verdict's equip script, on Caldera's forms.}

Spell Property TierAbility Auto
Weapon Property Hammer Auto
Actor Property PlayerRef Auto

Event OnEquipped(Actor akActor)
	If akActor && akActor == PlayerRef && TierAbility
		akActor.AddSpell(TierAbility, False)
	EndIf
EndEvent

Event OnUnequipped(Actor akActor)
	If !akActor || akActor != PlayerRef || !TierAbility
		Return
	EndIf
	Utility.Wait(0.5)
	Weapon w = akActor.GetEquippedWeapon(False)
	If !w || w != Hammer
		akActor.RemoveSpell(TierAbility)
	EndIf
EndEvent
