Scriptname ZFW_StoneScript extends ObjectReference
{Zenderal - Fog Wood: the Fogbound Stone (both the Whisperwood/pine-forest one the quest places and the exit stone
 in the wood). Activation goes to the arena quest. Being outside the quest, this script is also where the quest is
 stopped and started again ONCE per data version (ZFW_ArenaQuest.QUEST_VERSION): a quest instance captures its
 text-display globals and script properties when it starts, so a save whose quest started before the banners and
 the new properties existed never showed a wave number (2026-11-06). The quest keeps its placed stone through
 ZFW_Persist.}

ZFW_ArenaQuest Property Arena Auto

Event OnActivate(ObjectReference akActionRef)
	If akActionRef != Game.GetPlayer() || Arena == None
		Return
	EndIf
	If Arena.NeedsRestart()
		Arena.PrepareRestart()
		Arena.Stop()
		Utility.Wait(1.0)
		Arena.Start()
		Utility.Wait(1.5)                       ; OnInit, then the stone comes back from ZFW_Persist
	EndIf
	Arena.StoneActivated(Self)
EndEvent
