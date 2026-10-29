Scriptname ZP_TheHuntEffect extends ActiveMagicEffect
{The Hunt (Prophecy, Druidic, 2026-10-29): the power spends Cost Goodberries and calls Triumvirate's Gray Wolf - the
Wolf spell's summon, made to last until the wolf is killed. With Wolf Pack, SecondWolf calls another (the perk makes
room for it while the first wolf's effect is on). Without enough Goodberries nothing happens but a notification.}

Potion Property Goodberry Auto
Int Property Cost = 5 Auto
Spell Property Wolf Auto
Spell Property SecondWolf Auto
Perk Property WolfPack Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	If akCaster.GetItemCount(Goodberry) < Cost
		Debug.Notification("The Hunt needs " + Cost + " Goodberries.")
		Return
	EndIf
	akCaster.RemoveItem(Goodberry, Cost, True)
	Wolf.Cast(akCaster, akCaster)
	If SecondWolf && WolfPack && akCaster.HasPerk(WolfPack)
		Utility.Wait(0.5)
		SecondWolf.Cast(akCaster, akCaster)
	EndIf
EndEvent
