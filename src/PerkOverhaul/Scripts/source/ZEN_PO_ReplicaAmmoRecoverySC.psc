Scriptname ZEN_PO_ReplicaAmmoRecoverySC extends ActiveMagicEffect
{Trickster: Replica - each bow/musket hit on an actor has a Chance% chance to put one of the
equipped ammo into the target's inventory, to loot from the corpse. Stacks with the engine's own
iArrowInventoryChance roll. Lives on the ability the Replica perk (069CD6) grants. Needs
powerofthree's Papyrus Extender (OnWeaponHit, GetEquippedAmmo).}

Int Property Chance = 30 Auto
Keyword Property WeapTypeBow Auto

Actor kOwner

Event OnEffectStart(Actor akTarget, Actor akCaster)
	kOwner = akTarget
	PO3_Events_AME.RegisterForWeaponHit(Self)
EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	PO3_Events_AME.UnregisterForWeaponHit(Self)
EndEvent

Event OnWeaponHit(ObjectReference akTarget, Form akSource, Projectile akProjectile, Int aiHitFlagMask)
	If !akProjectile
		Return
	EndIf
	Actor kVictim = akTarget as Actor
	If !kVictim || kVictim == kOwner
		Return
	EndIf
	Weapon kWeapon = akSource as Weapon
	If !kWeapon || !kWeapon.HasKeyword(WeapTypeBow)
		Return
	EndIf
	If Utility.RandomInt(1, 100) > Chance
		Return
	EndIf
	Ammo kAmmo = PO3_SKSEFunctions.GetEquippedAmmo(kOwner)
	If kAmmo && kAmmo.IsPlayable()
		kVictim.AddItem(kAmmo, 1, true)
	EndIf
EndEvent
