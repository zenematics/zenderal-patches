Scriptname ZP_StingBroodMarkEffect extends ActiveMagicEffect
{Sting and Rise - Sting's brood. Rides on two hidden effects: the brood mark Sting's enchantment puts on every enemy
it hits (as long as the venom, dispelled when its bearer dies) and the venom-burst mark a dead spiderling's burst puts
on every enemy it hits (1 s, survives death, so a kill by the burst itself counts). When the mark ends on a corpse -
vanilla's soul trap test: OnEffectFinish, then IsDead - a Venom Spiderling bursts out of it: a short-lived ally placed
the way Prophecy's Legion of the Damned places its skeletons (PlaceActorAtMe, teammate; its own ability ends it after
15 s and bursts it in venom when it dies). One spiderling per corpse (Spawned faction), at most MaxSpiderlings alive.
Needs powerofthree's Papyrus Extender.}

ActorBase Property Spiderling Auto
Faction Property Spawned Auto
FormList Property Spiderlings Auto
Explosion Property SpawnBurst Auto

Int Property MaxSpiderlings = 5 AutoReadOnly
Float Property BaseHealth = 20.0 AutoReadOnly
Float Property HealthPerLevel = 2.0 AutoReadOnly
Float Property SeekRadius = 1500.0 AutoReadOnly
Int Property kActorCharacter = 62 AutoReadOnly

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	Actor player = Game.GetPlayer()
	If !akTarget || akCaster != player || !akTarget.IsDead() || akTarget.IsInFaction(Spawned)
		Return
	EndIf
	akTarget.AddToFaction(Spawned)
	If Living() >= MaxSpiderlings
		Return
	EndIf
	akTarget.PlaceAtMe(SpawnBurst)
	Actor spider = akTarget.PlaceActorAtMe(Spiderling)
	If !spider
		Return
	EndIf
	spider.SetActorValue("Health", BaseHealth + HealthPerLevel * player.GetLevel())
	spider.RestoreActorValue("Health", 100000.0)
	spider.SetPlayerTeammate(true)
	Spiderlings.AddForm(spider)
	Actor foe = Nearest(spider, player)
	If foe
		spider.StartCombat(foe)
	EndIf
EndEvent

; living spiderlings; the dead and the deleted leave the list
Int Function Living()
	Int alive = 0
	Int i = Spiderlings.GetSize()
	While i > 0
		i -= 1
		Form f = Spiderlings.GetAt(i)
		Actor s = f as Actor
		If !s || s.IsDead()
			If f
				Spiderlings.RemoveAddedForm(f)
			EndIf
		Else
			alive += 1
		EndIf
	EndWhile
	Return alive
EndFunction

Actor Function Nearest(Actor akFrom, Actor akPlayer)
	ObjectReference[] near = PO3_SKSEFunctions.FindAllReferencesOfFormType(akFrom, kActorCharacter, SeekRadius)
	Actor best = None
	Float bestDistance = 1000000.0
	Int i = 0
	While near && i < near.Length
		Actor a = near[i] as Actor
		If a && a != akFrom && !a.IsDead() && a.IsHostileToActor(akPlayer)
			Float d = akFrom.GetDistance(a)
			If d < bestDistance
				bestDistance = d
				best = a
			EndIf
		EndIf
		i += 1
	EndWhile
	Return best
EndFunction
