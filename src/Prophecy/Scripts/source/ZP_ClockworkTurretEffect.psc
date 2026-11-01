Scriptname ZP_ClockworkTurretEffect extends ActiveMagicEffect
{Prophecy Gadgets - Clockwork Turret (curator 2026-10-23: "target things on their own instead of where I aim").
Ordinator's ORD_DwarvenAutocannon_Script, rebuilt from its bytecode with the same properties, deploy and teardown,
and its own aim. Ordinator moved the aim marker along the player's facing and pitch every update, so the turret fired
parallel to the crosshair. Now each update the turret picks a target, turns to face it, puts the aim marker at its
chest (AimHeight of its height) and fires the shell at it:
  - the player's combat target, if it is valid and within TargetRange of the turret;
  - else the nearest valid actor within TargetRange (powerofthree's FindAllReferencesOfFormType).
Valid = alive, loaded, hostile to the player and already in combat, so a turret never starts a fight or breaks
stealth. No target: no shot. It fires wherever the player is (curator 2026-10-23): Ordinator's rule that it fires
only while the player stands within ORD_RemoteControlDist (12 ft) is gone; the property stays for the record's VMAD.
Kept from Ordinator: Overclock's second turret (ORD_AngleDelta) and its spin-up, now only on shots.}

Activator Property FXEmptyActivator Auto
MiscObject Property ORD_Smh_DwarvenAutocannon_Misc Auto
Perk Property ORD_Smh50_Electrobolt_Perk_50 Auto
Perk Property ORD_Smh80_SpinUp_Perk_80 Auto
Perk Property ORD_Smh70_FiringLine_Perk_70 Auto
Perk Property ORD_Smh30_RemoteControl_Perk_30 Auto
Float Property ORD_DistanceZ Auto
Float Property ORD_Min Auto
Float Property ORD_ShootZ Auto
Float Property ORD_AngleDelta Auto
Float Property ORD_SpeedUpDelta Auto
Float Property ORD_UpdateRate Auto
Float Property ORD_DistanceInFront Auto
Float Property ORD_RemoteControlDist Auto
Int Property ORD_Electrobolt Auto
Activator Property ORD_Smh_DwarvenAutocannon_Activator Auto
Activator Property ORD_Smh_DwarvenAutocannon_Activator_RemoteControl Auto
Spell Property ORD_Smh_DwarvenAutocannon_Spell_Proc Auto
Spell Property ORD_Smh_DwarvenAutocannon_Spell_Proc_Electrobolt Auto
Explosion Property ORD_Smh_DwarvenAutocannon_Explosion_Electrobolt Auto
Sound Property ORD_Smh_DwarvenAutocannon_Marker_Deploy Auto
Sound Property ORD_Smh_DwarvenAutocannon_Marker_Destroyed Auto
Float Property TargetRange = 2048.0 Auto
Float Property AimHeight = 0.6 Auto

Int Property kActorCharacter = 62 AutoReadOnly

Actor player
ObjectReference TheCannon
ObjectReference ShootStart
ObjectReference ShootAim
Float ShootRate
Int ShotCount
Bool SpinUp
Bool IsRemoteControl

Event OnEffectStart(Actor akTarget, Actor akCaster)
	player = akTarget
	ShootRate = ORD_UpdateRate
	If player.HasPerk(ORD_Smh50_Electrobolt_Perk_50)
		ShotCount = 0
	Else
		ShotCount = -9999
	EndIf
	ORD_Smh_DwarvenAutocannon_Marker_Deploy.Play(player)
	IsRemoteControl = player.HasPerk(ORD_Smh30_RemoteControl_Perk_30)
	Float a = player.GetAngleZ()
	If player.HasPerk(ORD_Smh70_FiringLine_Perk_70)
		a += ORD_AngleDelta
	EndIf
	If IsRemoteControl
		TheCannon = player.PlaceAtMe(ORD_Smh_DwarvenAutocannon_Activator_RemoteControl)
	Else
		TheCannon = player.PlaceAtMe(ORD_Smh_DwarvenAutocannon_Activator)
	EndIf
	TheCannon.MoveTo(player, ORD_DistanceInFront * Math.Sin(a), ORD_DistanceInFront * Math.Cos(a), ORD_DistanceZ, True)
	TheCannon.SetAngle(0.0, 0.0, a)
	ShootStart = TheCannon.PlaceAtMe(FXEmptyActivator)
	ShootStart.MoveTo(TheCannon, 0.0, 0.0, ORD_ShootZ, True)
	ShootAim = TheCannon.PlaceAtMe(FXEmptyActivator)
	ShootAim.MoveTo(TheCannon, 0.0, 0.0, ORD_ShootZ, True)
	player.RemoveItem(ORD_Smh_DwarvenAutocannon_Misc, 1, True)
	SpinUp = player.HasPerk(ORD_Smh80_SpinUp_Perk_80)
	RegisterForSingleUpdate(ORD_UpdateRate)
EndEvent

Event OnUpdate()
	If !TheCannon
		Return
	EndIf
	RegisterForSingleUpdate(ShootRate)
	Actor t = PickTarget()
	If !t
		Return
	EndIf
	TheCannon.SetAngle(0.0, 0.0, TheCannon.GetAngleZ() + TheCannon.GetHeadingAngle(t))
	ShootAim.MoveTo(t, 0.0, 0.0, t.GetHeight() * AimHeight, False)
	ShotCount += 1
	If ShotCount >= ORD_Electrobolt
		ShotCount = 0
		ShootStart.PlaceAtMe(ORD_Smh_DwarvenAutocannon_Explosion_Electrobolt)
		ORD_Smh_DwarvenAutocannon_Spell_Proc_Electrobolt.RemoteCast(ShootStart, player, ShootAim)
	Else
		ORD_Smh_DwarvenAutocannon_Spell_Proc.RemoteCast(ShootStart, player, ShootAim)
	EndIf
	If SpinUp && ShootRate > ORD_Min
		ShootRate -= ORD_SpeedUpDelta
	EndIf
EndEvent

Actor Function PickTarget()
	Actor best = player.GetCombatTarget()
	If best && IsValidTarget(best) && TheCannon.GetDistance(best) <= TargetRange
		Return best
	EndIf
	best = None
	Float bestDist = TargetRange + 1.0
	ObjectReference[] near = PO3_SKSEFunctions.FindAllReferencesOfFormType(TheCannon, kActorCharacter, TargetRange)
	Int i = 0
	While near && i < near.Length
		Actor a = near[i] as Actor
		If a && IsValidTarget(a)
			Float d = TheCannon.GetDistance(a)
			If d < bestDist
				best = a
				bestDist = d
			EndIf
		EndIf
		i += 1
	EndWhile
	Return best
EndFunction

Bool Function IsValidTarget(Actor a)
	Return a != player && !a.IsDead() && a.Is3DLoaded() && a.IsHostileToActor(player) && a.IsInCombat()
EndFunction

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	; no UnregisterForUpdate: the effect is already gone here and the call only logs an error
	ORD_Smh_DwarvenAutocannon_Marker_Destroyed.Play(TheCannon)
	TheCannon.Disable(True)
	TheCannon.Delete()
	ShootStart.Delete()
	ShootAim.Delete()
	TheCannon = None
	akTarget.AddItem(ORD_Smh_DwarvenAutocannon_Misc, 1, True)
EndEvent
