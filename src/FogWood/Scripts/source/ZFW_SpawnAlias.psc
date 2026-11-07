Scriptname ZFW_SpawnAlias extends ReferenceAlias
{Zenderal - Fog Wood: one of the 40 spawn aliases of ZFW_Arena, filled by ZFW_ArenaQuest.SpawnWave with a live
 spawn and cleared when it dies or the run ends. Its only job is evidence: every hit the spawn takes from another
 spawn is reported to the quest, which writes who hit whom with what to the Papyrus log (budgeted), so infighting
 is read from the log instead of guessed at (three guessed fixes, 2026-11-05/06).}

ZFW_ArenaQuest Property Arena Auto

Event OnHit(ObjectReference akAggressor, Form akSource, Projectile akProjectile, Bool abPowerAttack, Bool abSneakAttack, Bool abBashAttack, Bool abHitBlocked)
	Actor victim = GetReference() as Actor
	Actor aggressor = akAggressor as Actor
	If victim != None && aggressor != None && aggressor != Arena.PlayerRef
		Arena.SpawnHit(victim, aggressor, akSource, akProjectile)
	EndIf
EndEvent
