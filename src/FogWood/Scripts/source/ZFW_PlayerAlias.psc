Scriptname ZFW_PlayerAlias extends ReferenceAlias
{Zenderal - Fog Wood: the player alias of ZFW_Arena. Bleedout during a run (the player is essential for it)
 ends the run as a practice death; every game load re-checks the Fogbound Stone and the run's timer.}

ZFW_ArenaQuest Property Arena Auto

Event OnPlayerLoadGame()
	Arena.OnGameLoaded()
EndEvent

Event OnEnterBleedout()
	If Arena.Running
		Arena.EndRun(True)
	EndIf
EndEvent
