Scriptname ZP_CenturionGetOff extends ActiveMagicEffect
{Prophecy Gadgets - Centurion Armor: the "Climb out" entry of the Favorites-key menu (the last spell of the
SpellList). Ends the ride; ZP_CenturionRideOn's OnEffectFinish does the rest.}

Spell Property RideSpell Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Game.GetPlayer().DispelSpell(RideSpell)
EndEvent
