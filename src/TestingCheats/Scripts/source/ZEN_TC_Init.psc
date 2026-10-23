Scriptname ZEN_TC_Init extends Quest
{Testing Cheats - gives the player the power once per save (StartGameEnabled + RunOnce), existing saves included.}

Spell Property Power Auto

Event OnInit()
	Actor player = Game.GetPlayer()
	If !player.HasSpell(Power)
		player.AddSpell(Power, false)
	EndIf
EndEvent
