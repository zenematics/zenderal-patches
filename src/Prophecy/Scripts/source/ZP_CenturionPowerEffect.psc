Scriptname ZP_CenturionPowerEffect extends ActiveMagicEffect
{Prophecy Gadgets - Centurion Armor (lesser power, the tree's second capstone, curator 2026-11-13). One Centurion at a
time, remembered in CenturionList:
  - while the player pilots it (RideEffect running): climb out (dispel the ride; ZP_CenturionRideOn puts the armor back
    beside the player);
  - a living, enabled Centurion: recalled to the player's side;
  - otherwise a new one is placed in front of the player: a teammate on SureAI's follow package that fights for the
    player, and that the player can board by activating it (ZP_CenturionActor).
The Centurion is Ashihito Power Armor's Steam Centurion mech (Nexus 50659) on Enderal's Starling Centurion record.}

ActorBase Property CompanionBase Auto
FormList Property CenturionList Auto
Spell Property RideSpell Auto
MagicEffect Property RideEffect Auto
Sound Property ActivateSound Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Actor player = akCaster
	If player.HasMagicEffect(RideEffect)
		player.DispelSpell(RideSpell)
		Return
	EndIf
	Actor current = Current()
	Float angle = player.GetAngleZ()
	If current
		current.MoveTo(player, 160.0 * Math.Sin(angle), 160.0 * Math.Cos(angle), 0.0)
		current.SetAngle(0.0, 0.0, angle)
		Debug.Notification("The Starling Power Armor returns to your side.")
		Return
	EndIf
	ObjectReference placed = player.PlaceAtMe(CompanionBase, 1, False, False)
	Actor mech = placed as Actor
	If !mech
		Return
	EndIf
	mech.MoveTo(player, 200.0 * Math.Sin(angle), 200.0 * Math.Cos(angle), 0.0)
	mech.SetAngle(0.0, 0.0, angle + 180.0)
	mech.SetPlayerTeammate(True, False)
	CenturionList.Revert()
	CenturionList.AddForm(mech)
	If ActivateSound
		ActivateSound.Play(mech)
	EndIf
	Debug.Notification("Your Starling Power Armor arrives. Activate it to climb in; sneak and activate to dismiss it.")
EndEvent

; the remembered Centurion if it still lives and stands (not disabled: that is the one the player is inside)
Actor Function Current()
	If CenturionList.GetSize() == 0
		Return None
	EndIf
	Actor a = CenturionList.GetAt(0) as Actor
	If a && !a.IsDead() && !a.IsDisabled() && !a.IsDeleted()
		Return a
	EndIf
	Return None
EndFunction
