Scriptname ZP_CenturionRideOn extends ActiveMagicEffect
{Prophecy Gadgets - piloting the Centurion Armor (the ride: a lesser power ZP_CenturionActor casts on the player with
the Duration global as its duration). The player becomes the armor race in its steam suit and gets the control ability
(ZP_CenturionControl: attacks, power-attack hold, breath spells, flight); a beep + message at 90% of the time. When
the ride ends (time, or the power / the Favorites menu's Climb out dispelling it): race and gear back, the companion
re-enabled beside the player, and the cooldown cast (Cooldown global). Adapted from Ashihito Power Armor's
aaaCenturionRideOnScript; the mod re-summoned its furniture here, we bring the companion back.}

Race Property CenturionRace Auto
Armor Property SteamArmor Auto
FormList Property Gear Auto
GlobalVariable Property Duration Auto
GlobalVariable Property Cooldown Auto
Message Property RunoutMsg Auto
Sound Property AlertSound Auto
Spell Property CoolSpell Auto
Spell Property ControlSpell Auto
FormList Property CenturionList Auto

Actor player
Race originRace

Event OnEffectStart(Actor akTarget, Actor akCaster)
	player = Game.GetPlayer()
	player.SetGhost(True)
	originRace = player.GetRace()
	player.SetRace(CenturionRace)
	player.EquipItem(SteamArmor, True, True)
	player.AddSpell(ControlSpell, False)
	Game.EnablePlayerControls(True, False, False, True, False, False, False, False, 0)
	Game.FadeOutGame(False, True, 0.0, 0.8)
	player.SetGhost(False)
	RegisterForSingleUpdate((Duration.GetValueInt() * 0.9) as Float)
EndEvent

Event OnUpdate()
	If player
		If AlertSound
			AlertSound.Play(player)
		EndIf
		RunoutMsg.Show()
	EndIf
EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	UnregisterForUpdate()
	player.SetGhost(True)
	Game.FadeOutGame(True, True, 0.0, 0.5)
	Utility.Wait(0.4)
	Game.FadeOutGame(False, True, 30.0, 0.1)
	player.RemoveSpell(ControlSpell)
	player.SetRace(originRace)
	player.UnequipItem(SteamArmor, False, True)
	player.UnequipAll()
	player.RemoveItem(SteamArmor, 1, True, None)
	Utility.Wait(0.3)
	; the gear worn when boarding
	Int count = Gear.GetSize()
	Int i = 0
	While i < count && i < 31
		Form worn = Gear.GetAt(i)
		If worn && player.GetItemCount(worn) > 0
			player.EquipItem(worn, False, True)
		EndIf
		i += 1
	EndWhile
	Gear.Revert()
	; the armor steps out beside the player
	If CenturionList.GetSize() > 0
		Actor mech = CenturionList.GetAt(0) as Actor
		If mech && !mech.IsDead()
			Float angle = player.GetAngleZ()
			mech.MoveTo(player, 160.0 * Math.Sin(angle), 160.0 * Math.Cos(angle), 0.0)
			mech.SetAngle(0.0, 0.0, angle)
			mech.Enable()
		EndIf
	EndIf
	Game.FadeOutGame(False, True, 0.0, 0.8)
	player.SetGhost(False)
	Game.EnablePlayerControls()
	Int cool = Cooldown.GetValueInt()
	If cool >= 1
		CoolSpell.SetNthEffectDuration(0, cool)
		CoolSpell.Cast(player)
	EndIf
EndEvent
