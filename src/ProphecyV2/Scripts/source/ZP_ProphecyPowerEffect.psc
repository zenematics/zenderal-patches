Scriptname ZP_ProphecyPowerEffect extends ActiveMagicEffect
{Prophecy power (v2): enter the sanctum, or leave it if already inside. The quest does the work because this instant
effect ends as soon as the power is cast.}

ZP_ProphecySanctum Property MenuQuest Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	MenuQuest.RequestToggle()
EndEvent
