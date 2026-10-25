Scriptname ZP_ProphecyLevelWatch extends ReferenceAlias
{Player alias on ZP_ProphecyLevelWatch 0x80E (StartGameEnabled). Makes the Prophecy level-up prompts work on saves
that started before them: a quest new to the plugin starts when such a save loads, so this hooks
ZP_ProphecyMenu's level-up listener then and again on every load, and pays any point the save is already owed.}

Event OnInit()
	Hook()
EndEvent

Event OnPlayerLoadGame()
	Hook()
EndEvent

Function Hook()
	Utility.Wait(2.0)    ; let the load settle so a catch-up prompt is not lost behind the loading screen
	ZP_ProphecyMenu menu = Game.GetFormFromFile(0x807, "Zenderal - Prophecy.esp") as ZP_ProphecyMenu
	If menu
		menu.WatchLevelUps()
	EndIf
EndFunction
