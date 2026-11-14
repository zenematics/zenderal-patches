Scriptname ZET_BossEffect extends ActiveMagicEffect
{Zenderal - Enemy Threat: a boss's second phase (ZET_BossAbility, given by SPID to every ActorTypeBoss NPC).
The first time the boss is hit at or below half health it enrages (ZET_Enrage: Enderal's Fury shader, faster, and
ZET_BossPerk's +20% damage while it lasts), roars (Enderal's Primal Force shockwave, harmless; the player and
followers within RoarRadius are staggered) and calls AddCount enemies of its own kind (the generated table
ZET_AddBosses -> ZET_AddBases; bosses that are scripted quest kills are not in it, and nothing is called inside
the Fog Wood arena). Rank 1 in ZET_BossPhaseFaction marks that this boss has had its phase: later hits only renew
the enrage if it ran out. Constants are AutoReadOnly: a save keeps the values of Auto properties.}

Spell Property EnrageSpell Auto
MagicEffect Property EnrageEffect Auto
Spell Property RoarStagger Auto
Explosion Property RoarExplosion Auto
Faction Property PhaseFaction Auto
FormList Property AddBosses Auto
FormList Property AddBases Auto
Actor Property PlayerRef Auto

Float Property EnrageAt = 0.5 AutoReadOnly
Float Property RoarRadius = 600.0 AutoReadOnly
Int Property AddCount = 2 AutoReadOnly
Int Property FogWoodArenaFaction = 0x806 AutoReadOnly
String Property FogWoodPlugin = "Zenderal - Fog Wood.esp" AutoReadOnly

Actor boss
Bool busy

Event OnEffectStart(Actor akTarget, Actor akCaster)
	boss = akTarget
EndEvent

Event OnHit(ObjectReference akAggressor, Form akSource, Projectile akProjectile, Bool abPowerAttack, Bool abSneakAttack, Bool abBashAttack, Bool abHitBlocked)
	; OnHit runs on its own thread for every hit: the flag keeps two hits from both starting the phase
	If busy || !boss || boss.IsDead()
		Return
	EndIf
	If boss.GetActorValuePercentage("Health") > EnrageAt
		Return
	EndIf
	busy = True
	If boss.GetFactionRank(PhaseFaction) < 1
		boss.SetFactionRank(PhaseFaction, 1)
		EnrageSpell.Cast(boss, boss)
		Roar()
		CallAdds(akAggressor as Actor)
		Debug.Trace("[ZET boss] " + boss.GetDisplayName() + " " + boss + " enraged at " + boss.GetActorValuePercentage("Health"))
	ElseIf !boss.HasMagicEffect(EnrageEffect)
		EnrageSpell.Cast(boss, boss)   ; the enrage ran out or was dispelled: the buff again, no second roar or adds
	EndIf
	busy = False
EndEvent

Function Roar()
	boss.PlaceAtMe(RoarExplosion)
	StaggerIfNear(PlayerRef)
	Actor[] followers = PO3_SKSEFunctions.GetPlayerFollowers()
	Int i = 0
	While i < followers.Length
		StaggerIfNear(followers[i])
		i += 1
	EndWhile
EndFunction

Function StaggerIfNear(Actor akVictim)
	If akVictim && akVictim != boss && !akVictim.IsDead() && boss.GetDistance(akVictim) <= RoarRadius
		RoarStagger.Cast(boss, akVictim)
	EndIf
EndFunction

Function CallAdds(Actor akAggressor)
	Int i = AddBosses.Find(boss.GetActorBase())
	If i < 0 || InFogWoodArena()
		Return
	EndIf
	ActorBase addBase = AddBases.GetAt(i) as ActorBase
	Actor target = boss.GetCombatTarget()
	If !target
		target = akAggressor
	EndIf
	If !target
		target = PlayerRef
	EndIf
	Int n = 0
	While n < AddCount && addBase
		Actor add = boss.PlaceAtMe(addBase) as Actor
		If add
			add.StartCombat(target)
		EndIf
		n += 1
	EndWhile
	Debug.Trace("[ZET boss] " + boss.GetDisplayName() + " called " + AddCount + "x " + addBase + " against " + target)
EndFunction

; the Fog Wood arena (Patch Collection) tracks and sweeps its own spawns; adds it doesn't know of would stay behind
Bool Function InFogWoodArena()
	If Game.GetModByName(FogWoodPlugin) == 255
		Return False
	EndIf
	Faction arena = Game.GetFormFromFile(FogWoodArenaFaction, FogWoodPlugin) as Faction
	Return arena && boss.IsInFaction(arena)
EndFunction
