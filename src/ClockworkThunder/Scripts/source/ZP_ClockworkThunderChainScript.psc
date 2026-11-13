Scriptname ZP_ClockworkThunderChainScript extends ActiveMagicEffect
{Clockwork Thunder (Zenderal): the lightning bounces from enemy to enemy. The rifle's enchantment starts this on
the enemy a shot hits. That enemy gets only the ball (curator 2026-11-13: the lightning starts FROM the hit enemy
and strikes only the chained ones). Bolt (vanilla Chain Lightning's bolt, its explosion WITHOUT the engine's Chain
flag) jumps up to Jumps times: each time to the nearest living actor within Range of the last one struck that is
hostile to the player, not the player's teammate and not struck yet, JumpDelay apart so every jump is seen.
Each bolt is RemoteCast, blamed on the player, from an empty activator (EmptyActivator = FXEmptyActivator) at
AimHeight of the last one struck, StartOut units toward the next one (so it clears the struck body), at a second
one at AimHeight of the next. Never from the actor itself: an actor casts an aimed spell along its own facing,
so the first build's bolts flew off in whatever direction the struck enemy faced (curator 2026-11-13: "fires the
initial lightning in a random direction"). A non-actor source aims at the target: Ordinator's autocannon (Prophecy's
Clockwork Turret, ZP_ClockworkTurretEffect) fires the same way. The markers are deleted MarkerLife s after the last
bolt. Each bolt carries the damage and the level-gated stun (ZP_ClockworkThunderStunScript). The engine's own
chain was not used: its jumps are player-shooter projectiles that Hit Where You Aim turns back to the crosshair,
and its reach is the spell's Area (13 ft). ZenRemoteCastAim keeps these RemoteCasts on their own aim (they start
away from the player). Needs powerofthree's Papyrus Extender (FindAllReferencesOfFormType), as Prophecy's scripts
do. The effect has no duration, so everything after the first line runs on locals and Global functions.}

Spell Property Bolt Auto
Activator Property EmptyActivator Auto
Actor Property PlayerRef Auto

Int Property Jumps = 4 AutoReadOnly              ; 02-build-records.py CHAIN_JUMPS
Float Property Range = 700.0 AutoReadOnly        ; 02-build-records.py CHAIN_RANGE
Float Property JumpDelay = 0.15 AutoReadOnly
Float Property AimHeight = 0.6 AutoReadOnly      ; of the actor's height, as the Clockwork Turret aims
Float Property StartOut = 70.0 AutoReadOnly      ; at most half the gap
Float Property MarkerLife = 2.0 AutoReadOnly

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Spell boltSpell = Bolt
	Activator markerBase = EmptyActivator
	Actor thePlayer = PlayerRef
	Int maxJumps = Jumps
	Float reach = Range
	Float pause = JumpDelay
	Float height = AimHeight
	Float out = StartOut
	Float life = MarkerLife
	If !akTarget || !boltSpell || !markerBase || !thePlayer || akTarget == thePlayer
		Return
	EndIf
	Actor[] struck = new Actor[8]
	ObjectReference[] markers = new ObjectReference[16]
	struck[0] = akTarget
	Actor last = akTarget
	Int n = 1
	While n <= maxJumps && n < struck.Length
		Actor nextOne = NearestEnemy(last, thePlayer, struck, reach)
		If !nextOne
			n = maxJumps + 1
		Else
			Utility.Wait(pause)
			ObjectReference fromMarker = MarkerAt(last, nextOne, markerBase, height, out)
			ObjectReference toMarker = MarkerAt(nextOne, None, markerBase, height, 0.0)
			markers[2 * n - 2] = fromMarker
			markers[2 * n - 1] = toMarker
			boltSpell.RemoteCast(fromMarker, thePlayer, toMarker)
			struck[n] = nextOne
			last = nextOne
			n += 1
		EndIf
	EndWhile
	Utility.Wait(life)
	Int i = 0
	While i < markers.Length
		If markers[i]
			markers[i].Delete()
		EndIf
		i += 1
	EndWhile
EndEvent

; An empty activator at afHeight of akAt's height, afOut units (at most half the gap) toward akToward if given.
ObjectReference Function MarkerAt(Actor akAt, Actor akToward, Activator akBase, Float afHeight, Float afOut) Global
	ObjectReference m = akAt.PlaceAtMe(akBase, 1, False, False)
	Float ox = 0.0
	Float oy = 0.0
	If akToward
		Float dx = akToward.GetPositionX() - akAt.GetPositionX()
		Float dy = akToward.GetPositionY() - akAt.GetPositionY()
		Float flat = Math.Sqrt(dx * dx + dy * dy)
		If flat > 1.0
			Float d = afOut
			If d > flat * 0.5
				d = flat * 0.5
			EndIf
			ox = dx / flat * d
			oy = dy / flat * d
		EndIf
	EndIf
	m.MoveTo(akAt, ox, oy, akAt.GetHeight() * afHeight, False)
	Return m
EndFunction

Actor Function NearestEnemy(Actor akFrom, Actor akPlayer, Actor[] akStruck, Float afRange) Global
	ObjectReference[] near = PO3_SKSEFunctions.FindAllReferencesOfFormType(akFrom, 62, afRange)   ; 62 = Character
	Actor best = None
	Float bestDistance = afRange + 1.0
	Int i = 0
	While near && i < near.Length
		Actor a = near[i] as Actor
		If a && a != akPlayer && !a.IsDead() && !a.IsDisabled() && !a.IsPlayerTeammate() && a.IsHostileToActor(akPlayer) && akStruck.Find(a) < 0
			Float d = a.GetDistance(akFrom)
			If d < bestDistance
				best = a
				bestDistance = d
			EndIf
		EndIf
		i += 1
	EndWhile
	Return best
EndFunction
