Scriptname ZP_SendRavenEffect extends ActiveMagicEffect
{Send an Owl (Arcane Archery 4; was Send a Raven - the script keeps its name): a short effect on the target of a bow hit
(the gun hit spell). With no owl out, it places BirdBase above the player, on the player's side, stamps it, gives it
its Health and the RavenBrain ability, plays SpawnSound once and sets it on the target. BirdBase is Prophecy's Barn Owl
(Triumvirate's Call Raven creature wearing Mihail's owl1go.nif, no sound types; its strikes drain Magicka to the
player). With an owl out, the hit redirects it to the new target (and fetches it if it was left behind). One bird at a
time, kept in Ravens; it stays until it is killed. RavenBrain (ZP_RavenBrainEffect, on the bird) flies it and cleans
up when it dies - this effect owns nothing, because a hit-spell effect's own conditions are re-checked while it runs
and ended the first build's raven after 2 seconds.
Every bird this build places is stamped (MarkerAV = MarkerValue). A bird without the stamp is an older build's raven -
Triumvirate's record with its looping crow call - and is replaced here; RavenBrain removes it as well. (A base-record
check could not be trusted for a level-scaled creature.)}

FormList Property Ravens Auto
Faction Property PlayerFaction Auto
Spell Property RavenBrain Auto
ActorBase Property BirdBase Auto
Sound Property SpawnSound Auto
Float Property HealthBase = 50.0 Auto
Float Property HealthPerLevel = 5.0 Auto
Float Property FetchDistance = 3000.0 Auto
String Property MarkerAV = "Variable08" AutoReadOnly
Float Property MarkerValue = 7.0 AutoReadOnly

Event OnEffectStart(Actor akTarget, Actor akCaster)
	If !akCaster || akTarget.IsDead() || akTarget.IsPlayerTeammate()
		Return                                  ; a stray arrow into the owl or a follower sends nothing at them
	EndIf
	Actor current = None
	If Ravens.GetSize() > 0
		current = Ravens.GetAt(0) as Actor
	EndIf
	If current && current.GetActorValue(MarkerAV) != MarkerValue
		current.StopTranslation()
		current.Disable(True)                   ; an older build's raven: replace it
		current.Delete()
		current = None
	EndIf
	If current && !current.IsDead() && !current.IsDisabled()
		If !current.Is3DLoaded() || current.GetDistance(akCaster) > FetchDistance
			current.StopTranslation()
			current.MoveTo(akCaster, 0.0, 0.0, 150.0)
		EndIf
		If !akTarget.IsDead()
			current.StartCombat(akTarget)       ; one bird at a time: redirect it
		EndIf
		Return
	EndIf
	Ravens.Revert()
	Actor bird = akCaster.PlaceActorAtMe(BirdBase)
	If !bird
		Return
	EndIf
	bird.SetActorValue(MarkerAV, MarkerValue)   ; before RavenBrain, which removes unstamped birds
	Ravens.AddForm(bird)
	bird.RemoveFromAllFactions()
	bird.AddToFaction(PlayerFaction)
	bird.SetPlayerTeammate(True, False)
	bird.IgnoreFriendlyHits(True)
	bird.SetActorValue("Health", HealthBase + HealthPerLevel * akCaster.GetLevel())
	bird.MoveTo(akCaster, 0.0, 0.0, 150.0)
	bird.AddSpell(RavenBrain, False)
	If SpawnSound
		SpawnSound.Play(bird)
	EndIf
	If !akTarget.IsDead()
		bird.StartCombat(akTarget)
	EndIf
EndEvent
