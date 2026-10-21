Scriptname ZEN_GoblinRespawn extends Actor
{Zenderal - Goblins: a placed goblin comes back ZEN_GoblinRespawnDays in-game days after it died.
 The check runs when the goblin's 3D loads (OnLoad), i.e. when its cell comes into the loaded area,
 usually well before the player sees it. The engine's own cell reset (Respawn flag) still applies too.
 Also sets every goblin's base health to HealthScale of what the game first computed for it: our goblins
 take race Starting Health and Mihail's auto-calculate theirs, so no record value can cut both by 35%.
 Idempotent (always HealthScale x the remembered original), whether or not Reset() restores base health.
 No new properties (instances in existing saves keep theirs): the scale is a script constant.}

GlobalVariable Property GameDaysPassed Auto
GlobalVariable Property ZEN_GoblinRespawnDays Auto

Float DiedOn = -1.0
Float OriginalHealth = -1.0
Float HealthScale = 0.65

Function Weaken()
	If OriginalHealth < 0.0
		OriginalHealth = GetBaseActorValue("Health")
	EndIf
	Float target = OriginalHealth * HealthScale
	If GetBaseActorValue("Health") != target
		SetActorValue("Health", target)
	EndIf
EndFunction

Event OnDeath(Actor akKiller)
	DiedOn = GameDaysPassed.GetValue()
EndEvent

Event OnLoad()
	If DiedOn >= 0.0 && IsDead() && GameDaysPassed.GetValue() - DiedOn >= ZEN_GoblinRespawnDays.GetValue()
		DiedOn = -1.0
		Reset()
		RegisterForSingleUpdate(1.0)    ; re-apply once the reset has settled
	EndIf
	Weaken()
EndEvent

Event OnUpdate()
	Weaken()
EndEvent
