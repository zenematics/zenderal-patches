Scriptname ZP_CenturionControl extends ActiveMagicEffect
{Prophecy Gadgets - the Centurion Armor's controls while the player pilots it (an ability ZP_CenturionRideOn adds for
the ride and removes after). Ashihito Power Armor's aaaCenturionControlScript, kept as the author built it: the player
is a creature race with no attack input of its own, so the attack keys send the Steam Centurion graph's attack events
by movement direction; Activate held = power-attack mode (the FX smoke + the perk + PowerAttackSpell's burst at each
blow, 140 Stamina a swing); Shout held = the chosen breath spell (Favorites opens SelectMenu, one entry per SpellList
spell; the last, Climb out, ends the ride at once); Tween Menu held = flight (a translating invisible floor, 5 Magicka
every half second); the Sneak key = climb out (sneaking itself is off for the ride).
Most controls are disabled for the ride (menus, activation, dialogue): a pure war machine.
Changes from the mod: English notifications; the unused RocketFire spell dropped; only the player is controlled; the
Sneak-key exit and the menu's immediate Climb out (2026-11-13: the first test found no way out - the menu only picked
Climb out as the breath spell, to be cast with the Shout key).
2026-11-15 (renamed Starling Power Armor; curator: "add Shock Nova to the left Power attack and Chain Lightning on hit
to the Right power attacks ... only when piloting it"): a left-arm power blow places Flow State's Shock Nova explosion
at the armor as the blow lands; a right-arm power swing sets RightArm to 1, and ZenProphecyRage.dll casts Dragon's
Breath's chain lightning at the enemy the swing hits (then clears it; cleared here too 2 s after the swing). The
companion on its own (not piloted) never runs this script, so it keeps its standard attacks and steam.}

Spell Property PowerAttackSpell Auto
FormList Property SpellList Auto
Sound Property Fire Auto
Activator Property MovingFloor Auto
Perk Property PowerAttackPerk Auto
Message Property SelectMenu Auto
Spell Property RideSpell Auto
Explosion Property ShockNova Auto         ; ZP_Prophecy_FlowStateNova 0x93D: placed at the armor on a left power blow
GlobalVariable Property RightArm Auto     ; ZP_Centurion_RightArm: 1 during a right power swing, read by the Rage DLL
VisualEffect Property FireEffect Auto
VisualEffect Property FXDwarvenCenturion Auto
VisualEffect Property FXDwarvenCenturionArm01 Auto
VisualEffect Property FXDwarvenCenturionArm02 Auto

Actor he
Int Rkey
Int Lkey
Int shoutkey
Int Drawkey
Int menukey
Int jump
Int activate
Int sprint
Int Favoriteskey
Int sneakkey

Int answer01
Int soundID

Bool Power
Bool InAction
Bool Canfly

Float staminaref
Float posX
Float posY
Float posZ
Float AngZ

ObjectReference norimono
Spell Xspell

Event OnEffectStart(Actor Target, Actor Caster)
	If Target != Game.GetPlayer()
		Return
	EndIf
	Game.DisablePlayerControls(False, True, True, False, True, True, True, False, 0)
	he = Game.GetPlayer()
	Xspell = SpellList.GetAt(0) as Spell
	Lkey = Input.GetMappedKey("Left Attack/Block")
	Rkey = Input.GetMappedKey("Right Attack/Block")
	shoutkey = Input.GetMappedKey("Shout")
	jump = Input.GetMappedKey("Jump")
	Drawkey = Input.GetMappedKey("Ready Weapon")
	menukey = Input.GetMappedKey("Tween Menu")
	activate = Input.GetMappedKey("Activate")
	sprint = Input.GetMappedKey("Sprint")
	Favoriteskey = Input.GetMappedKey("Favorites")
	sneakkey = Input.GetMappedKey("Sneak")
	RegisterForKey(sneakkey)
	RegisterForKey(Lkey)
	RegisterForKey(Rkey)
	RegisterForKey(shoutkey)
	RegisterForKey(jump)
	RegisterForKey(Drawkey)
	RegisterForKey(menukey)
	RegisterForKey(activate)
	RegisterForKey(sprint)
	RegisterForKey(Favoriteskey)
	Debug.Trace("[ZP Starling] ride on: ShockNova=" + ShockNova + " RightArm=" + RightArm + " PowerAttackSpell=" + PowerAttackSpell)
	Debug.Notification("Starling Power Armor: attack keys swing the arms, hold Activate for power blows, hold Shout to breathe.")
	Utility.Wait(3.0)
	Debug.Notification("Hold Tween Menu to fly. Favorites picks the breath. Sneak key or Favorites > Climb out to get out.")
EndEvent

Function ClimbOut()
	If he && RideSpell
		he.DispelSpell(RideSpell)
	EndIf
EndFunction

Event OnKeyDown(Int KeyCode)
	If !he || he.IsDead() || Utility.IsInMenuMode()
		Return
	EndIf

	; ---------------------------------------------------------------- climb out
	If KeyCode == sneakkey
		ClimbOut()
		Return
	EndIf

	; ---------------------------------------------------------------- right arm
	If KeyCode == Rkey
		staminaref = he.GetActorValue("Stamina")
		If !he.IsWeaponDrawn()
			he.DrawWeapon()
		ElseIf !InAction
			InAction = True
			If Power
				If staminaref >= 30
					If he.GetAnimationVariableFloat("Direction") > 0.825 || he.GetAnimationVariableFloat("Direction") <= 0.125
						If he.GetAnimationVariableFloat("Speed") >= 5.0
							Debug.SendAnimationEvent(he, "attackStartForwardPowerRushRight")
						Else
							Debug.SendAnimationEvent(he, "attackStartForwardPowerRight")
						EndIf
					Else
						Debug.SendAnimationEvent(he, "attackStartForwardPowerRight")
					EndIf
					RightArm.SetValue(1)          ; the hit this swing lands chains lightning (ZenProphecyRage.dll)
					Debug.Trace("[ZP Starling] right power swing, RightArm=" + RightArm.GetValue())
					Utility.Wait(0.5)
					PowerAttackSpell.Cast(he)
					Utility.Wait(2.0)
					RightArm.SetValue(0)
					he.DamageActorValue("Stamina", 140)
				EndIf
			Else
				Float dir = he.GetAnimationVariableFloat("Direction")
				If dir > 0.825 || dir <= 0.125
					If he.GetAnimationVariableFloat("Speed") >= 5.0
						Debug.SendAnimationEvent(he, "attackStartStab")
						Utility.Wait(1.0)
					Else
						Debug.SendAnimationEvent(he, "attackStartChop")
						Utility.Wait(0.7)
					EndIf
				ElseIf dir > 0.375 && dir <= 0.625
					Debug.SendAnimationEvent(he, "attackStartBack")
					Utility.Wait(0.4)
					PowerAttackSpell.Cast(he)
					Utility.Wait(0.8)
				ElseIf dir > 0.125 && dir <= 0.375
					Debug.SendAnimationEvent(he, "attackStartSlash")
					Utility.Wait(0.7)
				Else
					Debug.SendAnimationEvent(he, "attackStartChop")
					Utility.Wait(0.7)
				EndIf
			EndIf
			InAction = False
		EndIf
		Return
	EndIf

	; ---------------------------------------------------------------- left arm
	If KeyCode == Lkey
		staminaref = he.GetActorValue("Stamina")
		If !he.IsWeaponDrawn()
			he.DrawWeapon()
		ElseIf !InAction
			InAction = True
			If Power
				If staminaref >= 30
					If he.GetAnimationVariableFloat("Direction") > 0.825 || he.GetAnimationVariableFloat("Direction") <= 0.125
						If he.GetAnimationVariableFloat("Speed") >= 5.0
							Debug.SendAnimationEvent(he, "attackStartForwardPowerRushLeft")
						Else
							Debug.SendAnimationEvent(he, "attackStartForwardPowerLeft")
						EndIf
					Else
						Debug.SendAnimationEvent(he, "attackStartForwardPowerLeft")
					EndIf
					Utility.Wait(0.5)
					PowerAttackSpell.Cast(he)
					If ShockNova
						ObjectReference nova = he.PlaceAtMe(ShockNova)   ; Flow State's nova round the armor (hostiles only)
						Debug.Trace("[ZP Starling] left power swing: nova placed " + nova)
					Else
						Debug.Trace("[ZP Starling] left power swing: ShockNova is None")
					EndIf
					Utility.Wait(1.6)
					he.DamageActorValue("Stamina", 140)
				EndIf
			Else
				Float dir = he.GetAnimationVariableFloat("Direction")
				If dir > 0.375 && dir <= 0.625
					Debug.SendAnimationEvent(he, "attackStartLeft")
					Utility.Wait(0.4)
					PowerAttackSpell.Cast(he)
					Utility.Wait(0.8)
				Else
					Debug.SendAnimationEvent(he, "bashStart")
					Utility.Wait(0.7)
				EndIf
			EndIf
			InAction = False
		EndIf
		Return
	EndIf

	; ---------------------------------------------------------------- breath (the chosen spell)
	If KeyCode == shoutkey
		If he.IsWeaponDrawn()
			If !InAction
				InAction = True
				Debug.SendAnimationEvent(he, "shoutstart")
				Utility.Wait(0.8)
				Debug.SendAnimationEvent(he, "shoutRelease")
				If Xspell
					Xspell.Cast(he)
				EndIf
			EndIf
		Else
			he.DrawWeapon()
		EndIf
		Return
	EndIf

	; ---------------------------------------------------------------- power-attack mode while Activate is held
	If KeyCode == activate
		If !InAction
			FXDwarvenCenturion.Play(he, -1)
			FXDwarvenCenturionArm01.Play(he, -1)
			FXDwarvenCenturionArm02.Play(he, -1)
			he.AddPerk(PowerAttackPerk)
			Power = True
		EndIf
		Return
	EndIf

	If KeyCode == Drawkey
		If !he.IsWeaponDrawn()
			he.DrawWeapon()
		ElseIf !InAction
			InAction = True
			he.SheatheWeapon()
			Utility.Wait(0.6)
			InAction = False
		EndIf
		Return
	EndIf

	; ---------------------------------------------------------------- flight while the Tween Menu key is held
	If KeyCode == menukey
		If !he.IsWeaponDrawn()
			he.DrawWeapon()
		ElseIf !InAction && !Canfly
			InAction = True
			Canfly = True
			Utility.Wait(0.001)
			GotoState("jet")
		EndIf
	EndIf

	If KeyCode == Favoriteskey
		If !InAction
			InAction = True
			GotoState("SpellSelectMenu")
		EndIf
		Return
	EndIf
EndEvent

Event OnKeyUp(Int KeyCode, Float HoldTime)
	If KeyCode == activate && Power
		FXDwarvenCenturion.Stop(he)
		FXDwarvenCenturionArm01.Stop(he)
		FXDwarvenCenturionArm02.Stop(he)
		he.RemovePerk(PowerAttackPerk)
		Power = False
		Return
	EndIf
	If KeyCode == shoutkey
		Utility.Wait(0.001)
		If he.IsWeaponDrawn()
			If HoldTime < 1
				Utility.Wait(1.0)
			EndIf
			he.InterruptCast()
			Debug.SendAnimationEvent(he, "shoutStop")
			InAction = False
		EndIf
		Return
	EndIf
EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	CenturionFinish()
EndEvent

Event OnDying(Actor akKiller)
	DeathProcess()
EndEvent

Event OnBeginState()
	Utility.Wait(0.1)
	InAction = False
EndEvent

; ================================================================ flight
State jet
	Event OnBeginState()
		Sound.StopInstance(soundID)
		FireEffect.Play(he)
		Debug.SendAnimationEvent(he, "shoutstart")
		If he.GetActorValue("Magicka") >= 3
			posX = he.GetPositionX()
			posY = he.GetPositionY()
			posZ = he.GetPositionZ() - 50
			AngZ = he.GetAngleZ()
			norimono = he.PlaceAtMe(MovingFloor)
			norimono.SetPosition(posX, posY, posZ)
			norimono.SetAngle(0, 0, 0)
			RegisterForUpdate(0.5)
			soundID = Fire.Play(he)
		EndIf
	EndEvent

	Event OnUpdate()
		posX = he.GetPositionX()
		posY = he.GetPositionY()
		posZ = he.GetPositionZ()
		AngZ = he.GetAngleZ()
		he.DamageActorValue("Magicka", 5)
		If norimono && he.GetActorValue("Magicka") >= 3
			norimono.TranslateTo(posX + Math.Sin(AngZ) * 600, posY + Math.Cos(AngZ) * 600, posZ + 1000, 0, 0, 0, 600.0, 0.01)
			Debug.SendAnimationEvent(he, "shoutstart")
		Else
			GotoState("Jetfinish")
		EndIf
	EndEvent

	Event OnTranslationComplete()
		GotoState("Jetfinish")
	EndEvent

	Event OnKeyUp(Int KeyCode, Float HoldTime)
		If KeyCode == menukey
			Utility.Wait(0.001)
			If HoldTime < 1
				Utility.Wait(1.0)
			EndIf
			Utility.Wait(0.01)
			GotoState("Jetfinish")
		EndIf
	EndEvent

	Event OnEffectFinish(Actor akTarget, Actor akCaster)
		CenturionFinish()
	EndEvent

	Event OnDying(Actor akKiller)
		DeathProcess()
	EndEvent
EndState

State Jetfinish
	Event OnBeginState()
		FireEffect.Stop(he)
		If norimono
			norimono.StopTranslation()
		EndIf
		Sound.StopInstance(soundID)
		UnregisterForUpdate()
		If norimono
			norimono.Delete()
			norimono = None
		EndIf
		InAction = False
		Utility.Wait(0.3)
		Debug.SendAnimationEvent(he, "shoutStop")
		Canfly = False
		GotoState("")
	EndEvent

	Event OnEffectFinish(Actor akTarget, Actor akCaster)
		CenturionFinish()
	EndEvent

	Event OnDying(Actor akKiller)
		DeathProcess()
	EndEvent
EndState

; ================================================================ the Favorites menu
State SpellSelectMenu
	Event OnBeginState()
		answer01 = SelectMenu.Show()
		If answer01 >= 0 && answer01 == SpellList.GetSize() - 1
			ClimbOut()        ; the last entry is Climb out: ends the ride now, not a breath to cast
		ElseIf answer01 >= 0 && answer01 < SpellList.GetSize()
			Spell picked = SpellList.GetAt(answer01) as Spell
			If picked
				Xspell = picked
			EndIf
		EndIf
		Utility.Wait(0.1)
		GotoState("")
	EndEvent

	Event OnEffectFinish(Actor akTarget, Actor akCaster)
		CenturionFinish()
	EndEvent

	Event OnDying(Actor akKiller)
		DeathProcess()
	EndEvent
EndState

; ================================================================ end of the ride (from every state's OnEffectFinish)
Function CenturionFinish()
	If !he
		Return
	EndIf
	If norimono
		norimono.StopTranslation()
	EndIf
	FireEffect.Stop(he)
	FXDwarvenCenturion.Stop(he)
	FXDwarvenCenturionArm01.Stop(he)
	FXDwarvenCenturionArm02.Stop(he)
	Sound.StopInstance(soundID)
	UnregisterForUpdate()
	Game.EnablePlayerControls()
	UnregisterForAllKeys()
	If norimono
		norimono.Delete()
		norimono = None
	EndIf
	he.RemovePerk(PowerAttackPerk)
	If RightArm
		RightArm.SetValue(0)
	EndIf
EndFunction

Function DeathProcess()
	If !he
		Return
	EndIf
	he.PlaySubGraphAnimation("StopEffect")
	Utility.Wait(1.0)
	FXDwarvenCenturion.Stop(he)
	FXDwarvenCenturionArm01.Stop(he)
	FXDwarvenCenturionArm02.Stop(he)
EndFunction
