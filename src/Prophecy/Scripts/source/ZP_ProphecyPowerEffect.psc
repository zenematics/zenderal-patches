Scriptname ZP_ProphecyPowerEffect extends ActiveMagicEffect
{Prophecy power: hands off to the ZP_ProphecyMenu quest script, which awards points and runs the menus. The menus
are not run here because this instant effect ends as soon as the power is cast.
2026-10-22: the menu's arrays also live here and are passed on every cast. A running quest keeps the property values
it started with in the save, so new perks never reached existing saves; a magic effect instance is created from the
plugin on each cast, so these are always the current ones. Written by src/Prophecy/tools/01-build-trees.py.}

ZP_ProphecyMenu Property MenuQuest Auto
Perk[] Property Perks Auto
String[] Property Descriptions Auto
String[] Property Images Auto
Int[] Property ParentA Auto
Int[] Property ParentB Auto
Int[] Property PowerPerk Auto
Form[] Property PowerSpell Auto
Int[] Property TreeStart Auto
Int[] Property GiftPerk Auto
Form[] Property GiftItem Auto
Int[] Property LevelReq Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	If Perks && TreeStart
		MenuQuest.Refresh(Perks, Descriptions, Images, ParentA, ParentB, PowerPerk, PowerSpell, TreeStart, GiftPerk, GiftItem, LevelReq)
	EndIf
	MenuQuest.RequestOpen()
EndEvent
