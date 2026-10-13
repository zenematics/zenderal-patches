Scriptname ZP_ProphecyPowerEffect extends ActiveMagicEffect
{Prophecy power: asks Custom Skills Framework to open the Prophecy perk tree.
CSF polls the ShowMenu global every frame and opens the tree when it is above 0.}

GlobalVariable Property ZP_ProphecyShowMenu Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	ZP_ProphecyShowMenu.SetValue(1)
EndEvent
