Scriptname ZP_RiseMoteEffect extends ActiveMagicEffect
{Sting and Rise - Rise's mote of sunlight. Rides on the mote effect (vanilla Mage Light in sun gold: a light on its
bearer and the orb above it) that Rise's enchantment puts on undead it strikes. Two things set off a fire nova from a
marked undead:
- its death: the mote is dispelled when its bearer dies; then - vanilla's soul trap test: OnEffectFinish, then
  IsDead - the corpse bursts;
- a successful Turn Undead on it (curator 2026-11-13): any effect of the engine's TurnUndead archetype applied to it
  that is still active TurnCheckSeconds later (a turn that fails its level check never stays), at most once every
  NovaCooldown seconds per undead (a concentration turn re-applies). The turned undead is burnt by its own nova too
  (curator: "doesn't actually damage the undead it comes from"): its mote is dispelled first (alive: no burst) and
  the nova's own mote replaces it, so it is refreshed, never doubled, and it still bursts when it dies.
The nova: BurstFX (Enderal's own fire nova, the Fire Arrow talent's Wayfarer burst: Fire Storm's ring of flame scaled
to Radius, no damage of its own) at the undead and Nova, remote-cast from the player (kill credit, Enderal's EP), on
every living actor within Radius hostile to the player. Nova puts a new mote on the undead among them first, so a
nova can set off more novas. Its fire damage is DamageBase + DamagePerLevel x the player's level, set on the spell
before each nova (SKSE SetNthEffectMagnitude; curator: 20 flat "doesn't seem to do much"). Needs powerofthree's
Papyrus Extender.}

Explosion Property BurstFX Auto
Spell Property Nova Auto

Float Property Radius = 300.0 AutoReadOnly          ; 02-build-records.py NOVA_RADIUS (checked there); tools/01 sizes the ring by it
Float Property DamageBase = 25.0 AutoReadOnly       ; 02-build-records.py NOVA_DAMAGE (checked there)
Float Property DamagePerLevel = 2.5 AutoReadOnly    ; 02-build-records.py NOVA_PER_LEVEL (checked there)
Int Property kTurnUndead = 24 AutoReadOnly          ; EffectArchetypes::ArchetypeID::kTurnUndead (PO3 GetEffectArchetypeAsInt)
Float Property TurnCheckSeconds = 0.25 AutoReadOnly
Float Property NovaCooldown = 2.0 AutoReadOnly

Actor me
Float lastTurnNova = -1000.0

Event OnEffectStart(Actor akTarget, Actor akCaster)
	me = akTarget
EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	If akTarget && akTarget.IsDead()
		Burst(Nova, BurstFX, akTarget, False, Radius, DamageBase, DamagePerLevel)
	EndIf
EndEvent

Event OnMagicEffectApply(ObjectReference akCaster, MagicEffect akEffect)
	If !akEffect || PO3_SKSEFunctions.GetEffectArchetypeAsInt(akEffect) != kTurnUndead
		Return
	EndIf
	Float now = Utility.GetCurrentRealTime()
	If now - lastTurnNova < NovaCooldown
		Return
	EndIf
	lastTurnNova = now                                ; claimed before the wait: two turn effects in one cast fire once
	Utility.Wait(TurnCheckSeconds)
	If !me || me.IsDead() || !PO3_SKSEFunctions.HasActiveMagicEffect(me, akEffect)
		lastTurnNova = -1000.0                        ; the turn failed: the next one may still set it off
		Return
	EndIf
	; everything the nova needs, read before this effect goes: the nova's own mote replaces it on the centre
	Spell nv = Nova
	Explosion fx = BurstFX
	Actor centre = me
	Float rad = Radius
	Float dmg = DamageBase
	Float perLevel = DamagePerLevel
	Dispel()
	Burst(nv, fx, centre, True, rad, dmg, perLevel)
EndEvent

Function Burst(Spell akNova, Explosion akFX, Actor akCentre, Bool abHitCentre, Float afRadius, Float afBase, Float afPerLevel) global
	Actor player = Game.GetPlayer()
	akNova.SetNthEffectMagnitude(1, afBase + afPerLevel * player.GetLevel())   ; effect 0 = the mote, 1 = the fire
	akCentre.PlaceAtMe(akFX)
	If abHitCentre && !akCentre.IsDead()
		akNova.RemoteCast(player, player, akCentre)
	EndIf
	ObjectReference[] near = PO3_SKSEFunctions.FindAllReferencesOfFormType(akCentre, 62, afRadius)   ; 62 = kActorCharacter
	Int i = 0
	While near && i < near.Length
		Actor a = near[i] as Actor
		If a && a != akCentre && !a.IsDead() && a.IsHostileToActor(player)
			akNova.RemoteCast(player, player, a)
		EndIf
		i += 1
	EndWhile
EndFunction
