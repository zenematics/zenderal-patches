Scriptname ZFW_RogueTake extends TopicInfo Hidden
{Zenderal - Fog Wood: the Rogue's "Take me to the Fog Wood." (dialogue response 0x823). Runs when his line ends;
 the arena quest starts the run (ZFW_ArenaQuest.RogueTake).}

ZFW_ArenaQuest Property Arena Auto

Function Fragment_0(ObjectReference akSpeakerRef)
	If Arena != None
		Arena.RogueTake(akSpeakerRef)
	EndIf
EndFunction
