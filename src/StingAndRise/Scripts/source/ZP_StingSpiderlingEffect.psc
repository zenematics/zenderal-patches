Scriptname ZP_StingSpiderlingEffect extends ActiveMagicEffect
{Sting and Rise - a Venom Spiderling's own ability (ActorEffect on its NPC record). Prophecy's Legion skeleton effect
(ZP_LegionSkeletonEffect) for a spider: the first time it starts it stamps the game time it dies at into Variable07
(LifeSeconds of real time at the current TimeScale, so a load does not reset it), checks the clock every PollSeconds
and kills the spiderling when its time is up. When it dies - killed or out of time - it bursts in venom: BurstFX at
its body (Blood Boil's burst on venom palettes, with the spider spit's splats) and Burst, remote-cast from the player
(kill credit, Enderal's EP) on every living actor within Radius hostile to the player; Burst's own mark makes an
enemy it kills burst into a spiderling too (ZP_StingBroodMarkEffect). Then it leaves Spiderlings and fades away 3 s
later. No inventory call on the dying actor (UnequipAll from OnDying crashed the game on a Legion archer).
Its hits web (curator 2026-11-13: its attacks "stop enemies in place with web", 3 s to break free): every weapon hit
(its bites) and magic hit (anything it spits or casts) on a living actor hostile to the player, not still in the
web's cooldown, gets WebSpell (rooted 3 s, then 3 s free), remote-cast from the spiderling and blamed on the player.
PO3's OnWeaponHit / OnMagicHit report the spiderling's own hits; the first build used a perk's combat hit spell,
which never went off on its bites (they carry the race's own attack spell). Each web is traced to the Papyrus log.
Needs powerofthree's Papyrus Extender.}

FormList Property Spiderlings Auto
Spell Property Burst Auto
Explosion Property BurstFX Auto
Spell Property WebSpell Auto
MagicEffect Property WebCooldown Auto

Float Property LifeSeconds = 15.0 AutoReadOnly       ; 02-build-records.py SPIDER_LIFE (checked there)
Float Property PollSeconds = 1.0 AutoReadOnly
Float Property Radius = 200.0 AutoReadOnly
Int Property kActorCharacter = 62 AutoReadOnly

Actor me

Event OnEffectStart(Actor akTarget, Actor akCaster)
	me = akTarget
	If me.IsDead()
		Return
	EndIf
	If me.GetActorValue("Variable07") <= 0.0
		Float timescale = (Game.GetForm(0x3A) as GlobalVariable).GetValue()     ; TimeScale
		me.SetActorValue("Variable07", Utility.GetCurrentGameTime() + LifeSeconds * timescale / 86400.0)
	EndIf
	PO3_Events_AME.RegisterForWeaponHit(Self)
	PO3_Events_AME.RegisterForMagicHit(Self)
	RegisterForSingleUpdate(PollSeconds)
EndEvent

Event OnWeaponHit(ObjectReference akTarget, Form akSource, Projectile akProjectile, Int aiHitFlagMask)
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
	RegisterForSingleUpdate(PollSeconds)
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
