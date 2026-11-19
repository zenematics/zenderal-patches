Scriptname ZP_OwlBowScript extends ObjectReference
{Owl Bow (Zenderal), on the bow: it needs no arrows. Equipping it remembers the player's arrows (OldAmmo), gives the
quiver ability (ZP_OwlBowQuiverEffect: keeps a hidden stock of ice arrows equipped and topped up after every shot);
unequipping takes the ability and every ice arrow away and puts the remembered arrows back on. The ice arrows are
non-playable (never in the inventory list, never picked up). Whisper's equip script shape.}

Spell Property QuiverAbility Auto
Ammo Property IceArrow Auto
Weapon Property Bow Auto
FormList Property OldAmmo Auto           ; at most one entry: the arrows equipped before the bow
Actor Property PlayerRef Auto

Event OnEquipped(Actor akActor)
	If !akActor || akActor != PlayerRef
		Return
	EndIf
	Form had = PO3_SKSEFunctions.GetEquippedAmmo(akActor)
	If had && had != IceArrow
		OldAmmo.Revert()
		OldAmmo.AddForm(had)
	EndIf
	akActor.AddSpell(QuiverAbility, False)
EndEvent

Event OnUnequipped(Actor akActor)
	If !akActor || akActor != PlayerRef
		Return
	EndIf
	Utility.Wait(0.5)
	If akActor.GetEquippedWeapon(False) == Bow
		Return                              ; re-equipped (or a second copy): keep the quiver
	EndIf
	akActor.RemoveSpell(QuiverAbility)
	Int n = akActor.GetItemCount(IceArrow)
	If n > 0
		akActor.RemoveItem(IceArrow, n, True)
	EndIf
	If OldAmmo.GetSize() > 0
		Ammo before = OldAmmo.GetAt(0) as Ammo
		If before && akActor.GetItemCount(before) > 0
			akActor.EquipItem(before, False, True)
		EndIf
	EndIf
EndEvent
