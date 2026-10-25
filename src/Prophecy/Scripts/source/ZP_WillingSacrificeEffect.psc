Scriptname ZP_WillingSacrificeEffect extends ActiveMagicEffect
{Prophecy Necromancy - A Willing Sacrifice (lesser power). Every summon and raised corpse the player commands
(powerofthree's GetCommandedActors) and every Legion of the Damned skeleton explodes, one after another. Each blast
deals HealthFraction of that summon's base Health to every living actor hostile to the player within Radius of it -
SureAI's own Corpse Explosion rule (_00E_FS_Entropy_CorpseExplosionSC: half the victim's base Health) - through Blast,
a hostile spell blamed on the player (kill credit, Enderal's EP). The look is Corpse Explosion's too: its shader, the
eldritch burst (BlastVisual, a copy without damage or screen effect) and its sound. Not its remains pile: an ash pile
takes the disintegrated actor's inventory, which would leave summon and Legion gear to loot.
The Dead Don't Forget (perk DeadDontForget): MagickaPerEnemy Magicka for every enemy the sacrifice hit, each counted
once. Usable again after the Cooldown spell's effect ends; with no summons it does nothing and costs no cooldown.
Forgotten Stories' forms are read with GetFormFromFile, so the plugin does not master it.}

Spell Property Blast Auto
Explosion Property BlastVisual Auto
FormList Property LegionList Auto
Perk Property DeadDontForget Auto
Spell Property Cooldown Auto
MagicEffect Property CooldownEffect Auto
Float Property Radius = 300.0 Auto
Float Property HealthFraction = 0.5 Auto
Float Property MagickaPerEnemy = 50.0 Auto

Int Property kActorCharacter = 62 AutoReadOnly

Actor player
Actor[] hit
Int hitCount

Event OnEffectStart(Actor akTarget, Actor akCaster)
	player = akCaster
	If player.HasMagicEffect(CooldownEffect)
		Debug.Notification("A Willing Sacrifice is not ready yet.")
		Return
	EndIf
	Actor[] commanded = PO3_SKSEFunctions.GetCommandedActors(player)
	Actor[] victims = new Actor[64]
	Int n = 0
	Int i = 0
	While commanded && i < commanded.Length && n < 64
		If commanded[i] && !commanded[i].IsDead() && commanded[i].Is3DLoaded()
			victims[n] = commanded[i]
			n += 1
		EndIf
		i += 1
	EndWhile
	i = 0
	Int legion = LegionList.GetSize()
	While i < legion && n < 64
		Actor s = LegionList.GetAt(i) as Actor
		If s && !s.IsDead() && s.Is3DLoaded()
			victims[n] = s
			n += 1
		EndIf
		i += 1
	EndWhile
	If n == 0
		Debug.Notification("You have no summons to sacrifice.")
		Return
	EndIf
	Cooldown.Cast(player, player)
	EffectShader fxs = Game.GetFormFromFile(0x02F280, "Enderal - Forgotten Stories.esm") as EffectShader     ; _00E_FS_Entropy_CorpseExplosionFXS
	Sound boom = Game.GetFormFromFile(0x02F2E3, "Enderal - Forgotten Stories.esm") as Sound                  ; _00E_FS_CorpseExplosionM
	hit = new Actor[128]
	hitCount = 0
	i = 0
	While i < n
		Explode(victims[i], fxs, boom)
		i += 1
	EndWhile
	If hitCount > 0 && player.HasPerk(DeadDontForget)
		player.RestoreActorValue("Magicka", MagickaPerEnemy * hitCount)
	EndIf
EndEvent

Function Explode(Actor akVictim, EffectShader akShader, Sound akSound)
	If akVictim.IsDead()
		Return
	EndIf
	Float damage = akVictim.GetBaseActorValue("Health") * HealthFraction
	Blast.SetNthEffectMagnitude(0, damage)
	If akShader
		akShader.Play(akVictim, 1.0)
	EndIf
	akVictim.SetCriticalStage(akVictim.CritStage_DisintegrateStart)
	Utility.Wait(0.2)
	ObjectReference[] near = PO3_SKSEFunctions.FindAllReferencesOfFormType(akVictim, kActorCharacter, Radius)
	Int i = 0
	While near && i < near.Length
		Actor a = near[i] as Actor
		If a && a != player && a != akVictim && !a.IsDead() && a.IsHostileToActor(player)
			Blast.RemoteCast(player, player, a)
			If hit.Find(a) < 0 && hitCount < hit.Length
				hit[hitCount] = a
				hitCount += 1
			EndIf
		EndIf
		i += 1
	EndWhile
	akVictim.PlaceAtMe(BlastVisual)
	If akSound
		akSound.Play(akVictim)
	EndIf
	akVictim.SetAlpha(0.0, True)
	akVictim.Kill(akVictim)              ; not the player: a raised enemy dying again gives no second EP
	akVictim.SetCriticalStage(akVictim.CritStage_DisintegrateEnd)
	Utility.Wait(0.15)                   ; one blast after another, and Blast's magnitude is read before the next set
EndFunction
