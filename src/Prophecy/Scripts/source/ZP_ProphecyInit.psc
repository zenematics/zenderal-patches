Scriptname ZP_ProphecyInit extends Quest
{Grants the Prophecy power once per save (StartGameEnabled + RunOnce).}

Spell Property ZP_ProphecyPower Auto

Event OnInit()
	Actor player = Game.GetPlayer()
	If !player.HasSpell(ZP_ProphecyPower)
		player.AddSpell(ZP_ProphecyPower, false)
	EndIf
EndEvent
