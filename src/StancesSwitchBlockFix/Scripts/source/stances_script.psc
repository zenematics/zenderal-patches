scriptName stances_script extends ActiveMagicEffect

import Debug
import Utility

Perk Property remove1 Auto
Perk Property remove2 Auto
Perk Property remove3 Auto
Perk Property add Auto
Spell Property icon Auto
Sound[] Property draw_sfx Auto


Event OnEffectStart(Actor akTarget, Actor akCaster)

	If !IsInMenuMode() && akTarget.IsWeaponDrawn()
		SwitchStance(akCaster)
	EndIf
	self.Dispel()

EndEvent


Function SwitchStance(Actor targetref)
	draw_sfx[targetref.GetEquippedItemType(1)].Play(targetref)
	icon.Cast(targetref)

	targetref.AddPerk(add)
	targetref.RemovePerk(remove1)
	targetref.RemovePerk(remove2)
	targetref.RemovePerk(remove3)	

	; ZSB: no block flick while dual wielding (a one-handed weapon in each hand). blockStop is lost here, so the
	; player stays in a block no key holds (ZenBlockReleaseFix logged one per stance key, 2026-11-12) and
	; first-person dual daggers stopped attacking. Dual wield has no block idle to refresh anyway.
	Int rightType = targetref.GetEquippedItemType(1)
	Int leftType = targetref.GetEquippedItemType(0)
	Bool dualWield = rightType >= 1 && rightType <= 4 && leftType >= 1 && leftType <= 4
	If !dualWield && !targetref.GetAnimationVariableBool("IsAttacking")
		SendAnimationEvent(targetref, "blockStart")
	;	wait(0.1)
		SendAnimationEvent(targetref, "blockStop")
	EndIf

EndFunction