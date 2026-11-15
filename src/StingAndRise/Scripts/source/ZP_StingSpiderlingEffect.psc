Scriptname ZP_StingSpiderlingEffect extends ActiveMagicEffect
{Sting and Rise - a Venom Spiderling's own ability (ActorEffect on its NPC record). Prophecy's Legion skeleton effect
(ZP_LegionSkeletonEffect) for a spider: the first time it starts it stamps the game time it dies at into Variable07
(LifeSeconds of real time at the current TimeScale, so a load does not reset it), checks the clock every PollSeconds
and kills the spiderling when its time is up. It runs at twice its race's speed (SpeedMult) and, whenever it has no
live hostile target, goes for the nearest enemy of the player within SeekRadius (curator 2026-11-14). Its bites land:
the game's melee check gives a creature its race's unarmed reach times its scale, and a spiderling is a small spider,
so on each of its own hit frames (HitFrame / weaponSwing) that no real hit followed within BiteWait, a combat target
within BiteReach and BiteArc of its facing still gets Bite (poison damage) and the web (curator: "not hitting very
easily"). When it dies - killed or out of time - it bursts in venom: BurstFX at
its body (Blood Boil's burst on venom palettes, with the spider spit's splats) and Burst, remote-cast from the player
(kill credit, Enderal's EP) on every living actor within Radius hostile to the player; Burst's own mark makes an
enemy it kills burst into a spiderling too (ZP_StingBroodMarkEffect). Then it leaves Spiderlings and fades away 3 s
later. No inventory call on the dying actor (UnequipAll from OnDying crashed the game on a Legion archer).
Its hits web (curator 2026-11-13: its attacks "stop enemies in place with web", 3 s to break free): every weapon hit
(its bites) and magic hit (anything it spits or casts) on a living actor hostile to the player, not still in the
web's cooldown, gets WebSpell (rooted 6 s since 2026-11-15, was 3; then 3 s free), remote-cast from the spiderling and blamed on the player.
PO3's OnWeaponHit / OnMagicHit report the spiderling's own hits; the first build used a perk's combat hit spell,
which never went off on its bites (they carry the race's own attack spell). Each web is traced to the Papyrus log.
Needs powerofthree's Papyrus Extender.}

FormList Property Spiderlings Auto
Spell Property Burst Auto
Explosion Property BurstFX Auto
Spell Property WebSpell Auto
MagicEffect Property WebCooldown Auto
Spell Property Bite Auto

Float Property LifeSeconds = 30.0 AutoReadOnly       ; 02-build-records.py SPIDER_LIFE (checked there)
Float Property SpeedMult = 200.0 AutoReadOnly        ; 02-build-records.py SPIDER_SPEED (checked there): twice the race's speed
Float Property PollSeconds = 0.5 AutoReadOnly        ; the lifetime clock and the hunt
Float Property SeekRadius = 2500.0 AutoReadOnly      ; a spiderling with no live target goes for the nearest enemy within this
Float Property Radius = 200.0 AutoReadOnly
Float Property BiteReach = 110.0 AutoReadOnly        ; 02-build-records.py BITE_REACH (checked there): centre to centre
Float Property BiteArc = 70.0 AutoReadOnly           ; degrees either side of its facing
Float Property BiteWait = 0.15 AutoReadOnly          ; a real hit within this of the hit frame counts instead
Int Property kActorCharacter = 62 AutoReadOnly

Actor me
Int hasteChecks = 0
Float lastRealHit = -1000.0
Float lastSwing = -1000.0

Event OnEffectStart(Actor akTarget, Actor akCaster)
	me = akTarget
	If me.IsDead()
		Return
	EndIf
	If me.GetActorValue("Variable07") <= 0.0
		Float timescale = (Game.GetForm(0x3A) as GlobalVariable).GetValue()     ; TimeScale
		me.SetActorValue("Variable07", Utility.GetCurrentGameTime() + LifeSeconds * timescale / 86400.0)
	EndIf
	Haste()
	PO3_Events_AME.RegisterForWeaponHit(Self)
	PO3_Events_AME.RegisterForMagicHit(Self)
	RegisterForAnimationEvent(me, "HitFrame")
	RegisterForAnimationEvent(me, "weaponSwing")
	RegisterForSingleUpdate(PollSeconds)
EndEvent

; a bite's hit frame: if the game's own (tiny-reach) check did not land it, land it here
Event OnAnimationEvent(ObjectReference akSource, String asEventName)
	Float now = Utility.GetCurrentRealTime()
	If now - lastSwing < 0.3                         ; HitFrame and weaponSwing of one bite
		Return
	EndIf
	lastSwing = now
	Utility.Wait(BiteWait)
	If !me || me.IsDead() || lastRealHit >= now
		Return
	EndIf
	Actor player = Game.GetPlayer()
	Actor victim = me.GetCombatTarget()
	If !victim || victim.IsDead() || !victim.IsHostileToActor(player)
		Return
	EndIf
	If me.GetDistance(victim) > BiteReach || Math.abs(me.GetHeadingAngle(victim)) > BiteArc
		Return
	EndIf
	Bite.RemoteCast(me, player, victim)
	Web(victim)
	Debug.Trace("[ZP Sting] spiderling " + me + " bite landed on " + victim + " (assist)")
EndEvent

; curator 2026-11-14: "twice as fast ... very quickly seek and attack targets". SpeedMult only reaches the actor's
; movement when its speed is recalculated, which a carry-weight change forces; done again on the first two polls in
; case the spiderling had no 3D yet when its ability started
Function Haste()
	If me.GetActorValue("SpeedMult") != SpeedMult
		me.SetActorValue("SpeedMult", SpeedMult)
	EndIf
	me.ModActorValue("CarryWeight", 0.1)
	me.ModActorValue("CarryWeight", -0.1)
EndFunction

; no live hostile target: straight at the nearest enemy of the player (rather than trotting back to the player)
Function Seek()
	Actor player = Game.GetPlayer()
	Actor current = me.GetCombatTarget()
	If current && !current.IsDead() && current.IsHostileToActor(player)
		Return
	EndIf
	ObjectReference[] near = PO3_SKSEFunctions.FindAllReferencesOfFormType(me, kActorCharacter, SeekRadius)
	Actor best = None
	Float bestDistance = 1000000.0
	Int i = 0
	While near && i < near.Length
		Actor a = near[i] as Actor
		If a && a != me && !a.IsDead() && a.IsHostileToActor(player)
			Float d = me.GetDistance(a)
			If d < bestDistance
				bestDistance = d
				best = a
			EndIf
		EndIf
		i += 1
	EndWhile
	If best
		me.StartCombat(best)
	EndIf
EndFunction

Event OnWeaponHit(ObjectReference akTarget, Form akSource, Projectile akProjectile, Int aiHitFlagMask)
	lastRealHit = Utility.GetCurrentRealTime()
	Web(akTarget as Actor)
EndEvent

Event OnMagicHit(ObjectReference akTarget, Form akSource, Projectile akProjectile)
	If akSource != WebSpell && akSource != Burst
		Web(akTarget as Actor)
	EndIf
EndEvent

Function Web(Actor akVictim)
	Actor player = Game.GetPlayer()
	If !me || me.IsDead() || !akVictim || akVictim == me || akVictim.IsDead() || !akVictim.IsHostileToActor(player)
		Return
	EndIf
	If akVictim.HasMagicEffect(WebCooldown)
		Return
	EndIf
	WebSpell.RemoteCast(me, player, akVictim)
	Debug.Trace("[ZP Sting] spiderling " + me + " webbed " + akVictim)
EndFunction

Event OnUpdate()
	If !me || me.IsDead()
		Return
	EndIf
	If Utility.GetCurrentGameTime() >= me.GetActorValue("Variable07")
		me.Kill(me)
		Return
	EndIf
	RegisterForSingleUpdate(PollSeconds)                 ; first: an error below must not end the clock
	If hasteChecks < 2
		hasteChecks += 1
		Haste()
	EndIf
	Seek()
EndEvent

Event OnDying(Actor akKiller)
	Actor player = Game.GetPlayer()
	me.PlaceAtMe(BurstFX)
	ObjectReference[] near = PO3_SKSEFunctions.FindAllReferencesOfFormType(me, kActorCharacter, Radius)
	Int i = 0
	While near && i < near.Length
		Actor a = near[i] as Actor
		If a && a != me && !a.IsDead() && a.IsHostileToActor(player)
			Burst.RemoteCast(player, player, a)
		EndIf
		i += 1
	EndWhile
	Spiderlings.RemoveAddedForm(me)
	Utility.Wait(3.0)
	If !me.IsDisabled()
		me.Disable(True)
	EndIf
	me.Delete()
EndEvent
