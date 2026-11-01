Scriptname ZP_RavenBrainEffect extends ActiveMagicEffect
{Send a Raven's raven: an ability on the raven (ZP_SendRavenEffect adds it). A placed raven never moved on its own in
game (2026-10-23), so this flies it: every PollSeconds it picks its fight - its combat target, else the player's - and
TranslateTo's a point at head height in front of that enemy until it is within AttackRange, then StopTranslation so its
own attacks land. With no fight it keeps behind the player's shoulder. Left more than LeashDistance behind, it is
moved to the player. It stays until it is killed; then it leaves Ravens and its body is removed. While it lives, every
poll restores PlayerMagickaPerSecond x PollSeconds Magicka to the player (Andrasta's Owl, curator 2026-10-23: +2/s).}

FormList Property Ravens Auto
Float Property FlySpeed = 900.0 Auto          ; units per second
Float Property AttackRange = 180.0 Auto
Float Property HoverHeight = 110.0 Auto       ; above an enemy's feet: about head height
Float Property StandOff = 70.0 Auto           ; in front of an enemy's face
Float Property FollowDistance = 250.0 Auto
Float Property LeashDistance = 3000.0 Auto
Float Property PollSeconds = 0.5 Auto
Float Property PlayerMagickaPerSecond = 2.0 Auto  ; Andrasta's Owl: the player's Magicka regen while the owl lives

Actor raven
Actor player
Int ghostLeft          ; polls left as a ghost (3 = 1.5 s after the player's last draw/attack)
Bool ghosted

Event OnEffectStart(Actor akTarget, Actor akCaster)
	raven = akTarget
	player = Game.GetPlayer()
	RegisterForSingleUpdate(PollSeconds)
EndEvent

Event OnUpdate()
	If !raven || raven.IsDead() || raven.IsDisabled()
		Return
	EndIf
	If raven.GetActorValue("Variable08") != 7.0
		; an older build's raven (Triumvirate's record, looping crow call) - including ones no longer in Ravens that
		; this ability kept following the player: remove it (ZP_SendRavenEffect stamps every bird it places)
		raven.StopTranslation()
		raven.Disable(True)
		raven.Delete()
		Return
	EndIf
	If PlayerMagickaPerSecond > 0.0
		player.RestoreActorValue("Magicka", PlayerMagickaPerSecond * PollSeconds)
	EndIf
	; the player's arrows pass through it (curator 2026-10-23): a ghost while the player draws or attacks and for
	; GhostPolls polls after (an arrow still in flight), solid otherwise so enemies can still kill it. The perk's
	; friendly-fire immunity zeroes damage, but only a ghost lets the arrow fly on.
	If player.GetAnimationVariableBool("bBowDrawn") || player.GetAnimationVariableBool("IsAttacking")
		ghostLeft = 3
	ElseIf ghostLeft > 0
		ghostLeft -= 1
	EndIf
	If (ghostLeft > 0) != ghosted
		ghosted = ghostLeft > 0
		raven.SetGhost(ghosted)
	EndIf
	If raven.GetDistance(player) > LeashDistance || (raven.GetParentCell() != player.GetParentCell() && player.IsInInterior())
		raven.StopTranslation()
		raven.MoveTo(player, 0.0, 0.0, 150.0)
	EndIf
	Actor t = raven.GetCombatTarget()
	If !t || t.IsDead()
		t = player.GetCombatTarget()
		If t && !t.IsDead()
			raven.StartCombat(t)
		EndIf
	EndIf
	If t && !t.IsDead()
		If raven.GetDistance(t) > AttackRange
			FlyNear(t, StandOff, HoverHeight)
		Else
			raven.StopTranslation()
		EndIf
	ElseIf raven.GetDistance(player) > FollowDistance
		FlyNear(player, -80.0, 170.0)          ; behind and above the player's shoulder
	Else
		raven.StopTranslation()
	EndIf
	RegisterForSingleUpdate(PollSeconds)
EndEvent

Function FlyNear(ObjectReference akRef, Float afStandOff, Float afHeight)
	Float a = akRef.GetAngleZ()
	Float x = akRef.GetPositionX() + afStandOff * Math.Sin(a)
	Float y = akRef.GetPositionY() + afStandOff * Math.Cos(a)
	Float z = akRef.GetPositionZ() + afHeight
	Float face = raven.GetAngleZ() + raven.GetHeadingAngle(akRef)
	raven.TranslateTo(x, y, z, 0.0, 0.0, face, FlySpeed, 0.0)
EndFunction

Event OnDying(Actor akKiller)
	Ravens.Revert()
	raven.StopTranslation()
	Utility.Wait(3.0)
	raven.Disable(True)
	raven.Delete()
EndEvent
