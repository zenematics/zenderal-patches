Scriptname ZEN_ArkGateSiegeQuestScript extends Quest
{Gives the player the perk that opens Castle Quarters gate 09EECD during the Ark siege.
Start-game enabled, so it also starts on the first load of an existing save.}

Perk Property ZEN_ArkGateSiegeOpenPerk Auto

Event OnInit()
	Actor player = Game.GetPlayer()
	If !player.HasPerk(ZEN_ArkGateSiegeOpenPerk)
		player.AddPerk(ZEN_ArkGateSiegeOpenPerk)
	EndIf
EndEvent
