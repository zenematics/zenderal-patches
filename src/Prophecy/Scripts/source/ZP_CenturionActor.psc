Scriptname ZP_CenturionActor extends Actor
{Prophecy Gadgets - the Centurion Armor companion (on the NPC record). Activating it boards it: the player's worn gear
is remembered in Gear, the player climbs in (the pull-chain idle, a fade), and the ride (ZP_CenturionRideOn, duration
= the Duration global) switches the player to the armor race; the companion itself is disabled meanwhile and put back
beside the player when the ride ends. Sneak-activate dismisses it. Boarding is refused while the cooldown effect runs.
Adapted from Ashihito Power Armor's aaaCenturionFurnitureActivateScript (a placed furniture in the mod; here the mech
is the companion itself), minus its reactor chest and the humanoid suit check.}

Spell Property RideSpell Auto
MagicEffect Property CoolEffect Auto
Message Property CoolMsg Auto
FormList Property Gear Auto
GlobalVariable Property Duration Auto
Sound Property EquipSound Auto
FormList Property CenturionList Auto

Bool busy

Event OnActivate(ObjectReference akActionRef)
	Actor player = Game.GetPlayer()
	If akActionRef != player || busy || IsDead()
		Return
	EndIf
	If player.IsSneaking()
		busy = True
		Debug.Notification("The Centurion Armor powers down.")
		CenturionList.Revert()
		Disable()
		Delete()
		Return
	EndIf
	If player.HasMagicEffect(CoolEffect)
		CoolMsg.Show()
		Return
	EndIf
	busy = True
	Game.DisablePlayerControls()
	If player.IsWeaponDrawn()
		player.SheatheWeapon()
		Utility.Wait(2.2)
	EndIf
	player.SetGhost(True)
	; no Game.ForceThirdPerson here: Improved Camera turns a scripted one into its head camera (ZenICSheatheFix log,
	; 2026-11-13); ZenICSheatheFix 1.9.0 puts the ride in a vanilla third person the frame the race swaps
	Debug.SendAnimationEvent(player, "IdlePullChain")
	If EquipSound
		EquipSound.Play(self)
	EndIf
	Utility.Wait(0.7)
	; what the player wears, so the ride can put it back
	Gear.Revert()
	Int slot = 0
	While slot < 31
		Form worn = player.GetWornForm(Math.LeftShift(1, slot))
		If worn
			Gear.AddForm(worn)
		EndIf
		slot += 1
	EndWhile
	Game.FadeOutGame(True, True, 0.0, 1.0)
	Utility.Wait(0.9)
	Game.FadeOutGame(False, True, 30.0, 0.1)    ; stays dark until the ride's own fade-in
	player.UnequipAll()
	RideSpell.SetNthEffectDuration(0, Duration.GetValueInt())
	; the mech steps aside: the player IS the armor until the ride ends (ZP_CenturionRideOn re-enables it)
	Disable()
	player.SetGhost(False)
	RideSpell.Cast(player)
	Game.EnablePlayerControls(True, False, False, True, False, False, False, False, 0)
	busy = False
EndEvent

Event OnDeath(Actor akKiller)
	; a destroyed armor can be called again
	If CenturionList.GetSize() > 0 && CenturionList.GetAt(0) == self
		CenturionList.Revert()
	EndIf
EndEvent
