Scriptname ZP_IceShotEffect extends ActiveMagicEffect
{Ice Shot (Arcane Archery 3): the lesser power. Bows only; costs MagickaCost (a lesser power has no cost of its own,
so it is taken here). Hands out ArrowCount ice arrows and equips them, remembering the ammo that was equipped in
OldAmmo (unless that was already ice arrows). Nothing else lives here: in game (2026-10-23) this effect ended early for
an unknown reason and took the unfired arrows with it, so the arrows are never taken back, the old ammo comes back
through ZP_IceShotWatcherEffect (an ability from the perk) once the ice arrows are spent, and the freeze is cast by
ZP_IceShotTriggerEffect on the arrow's hit (Flame Shot's explosion delivery missed big creatures - bears).}

Ammo Property IceArrow Auto
FormList Property AmmoList Auto              ; _00E_A1_FirearrowAmmoFormlist: the ammo the old one is looked up in
FormList Property OldAmmo Auto               ; the ammo to put back once the ice arrows are spent
GlobalVariable Property Remaining Auto       ; ice shots left from this cast - ZP_IceShotWatcherEffect counts it down
Int Property ArrowCount = 3 Auto
Float Property MagickaCost = 50.0 Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Actor player = akCaster
	If player.GetEquippedItemType(1) != 7
		Debug.Notification("Ice Shot needs a bow.")
		Return
	EndIf
	If player.GetActorValue("Magicka") < MagickaCost
		Debug.Notification("You do not have enough Magicka for Ice Shot.")
		Return
	EndIf
	player.DamageActorValue("Magicka", MagickaCost)
	Ammo current = FindEquippedAmmo(player)
	If current && current != IceArrow
		OldAmmo.Revert()
		OldAmmo.AddForm(current)
	EndIf
	; exactly ArrowCount per cast: leftovers (from a cast not fired out, or arrows put back) go first (in game 2026-10-23
	; 15-17 had piled up, so the "out of ice arrows" restore never came)
	Int held = player.GetItemCount(IceArrow)
	If held > 0
		player.RemoveItem(IceArrow, held, True)
	EndIf
	player.AddItem(IceArrow, ArrowCount, True)
	player.EquipItem(IceArrow, False, True)
	Remaining.SetValue(ArrowCount)
EndEvent

Ammo Function FindEquippedAmmo(Actor player)
	Int i = AmmoList.GetSize() - 1
	While i >= 0
		Ammo a = AmmoList.GetAt(i) as Ammo
		If a && player.IsEquipped(a)
			Return a
		EndIf
		i -= 1
	EndWhile
	Return None
EndFunction
