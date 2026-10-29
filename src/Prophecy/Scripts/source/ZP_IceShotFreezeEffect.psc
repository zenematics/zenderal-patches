Scriptname ZP_IceShotFreezeEffect extends ActiveMagicEffect
{Ice Shot's freeze, on the target (every ice arrow's explosion enchantment applies it - 100%, curator 2026-10-23).
The freeze is SureAI's own (_00E_FrozenMEScript: AI off, Paralysis 1) done here directly, with Enderal's frozen look
(the ice-form shader its Frozen effect uses) and Arctic Wind's freeze sound. The first build added Arctic Wind's
_00E_A1_ArcticWindFrozenAb behind a 35% roll and Arctic Wind's level cap (and that ability's script skips targets under
10% Health); in game nothing froze. Now every hit freezes for the effect's duration, except MagicNoFreeze targets.
While frozen, the player's next bow hit (after ArmDelay, so the freezing shot itself cannot shatter) shatters the
target: SureAI's ShatterEnemy, copied, with only its frost burst (no debris). Essential actors freeze but never
shatter. Bows only (weapon type 7).}

Keyword Property MagicNoFreeze Auto
Keyword Property ActorTypeNPC Auto
Race Property DraugrRace Auto
EffectShader Property IceShader Auto          ; FrostIceFormFXShader02 0DC20E - _00E_Frozen_ME's look
Sound Property FreezeSound Auto               ; _00E_A1_ArcticWindFreezeM
Explosion Property ShatterExplosion Auto      ; _00E_FrostShatteringExplosion
Explosion Property ShatterExplosion02 Auto    ; _00E_FrostShatteringExplosion02
Explosion Property IceGoreExplosion Auto      ; _00E_FS_MAGIceGoreExplosion
Activator Property ShatteredPile Auto         ; _00E_ShatteredEnemyPile
Sound Property ImpactIce Auto                 ; WPNImpactBladeVsIce
Float Property ArmDelay = 0.5 Auto

Actor target
Actor player
Bool frozen
Bool armed

Event OnEffectStart(Actor akTarget, Actor akCaster)
	target = akTarget
	player = Game.GetPlayer()
	If target.IsDead() || target.HasKeyword(MagicNoFreeze) || target.IsPlayerTeammate()
		Return                                  ; never freeze (and later shatter) a follower or Andrasta's Owl
	EndIf
	; weak enemies only (curator 2026-10-29: "people are 2 shotting bosses" - the shatter is a kill): no higher level
	; than the player, and never a unique actor (bosses, named enemies). The others keep the frost damage only
	If target.GetLevel() > player.GetLevel() || target.GetLeveledActorBase().IsUnique()
		Return
	EndIf
	frozen = True
	FreezeSound.Play(target)
	IceShader.Play(target)
	target.EnableAI(False)
	target.SetActorValue("Paralysis", 1.0)
	RegisterForSingleUpdate(ArmDelay)
EndEvent

Event OnUpdate()
	armed = frozen
EndEvent

Event OnHit(ObjectReference akAggressor, Form akSource, Projectile akProjectile, Bool abPowerAttack, Bool abSneakAttack, Bool abBashAttack, Bool abHitBlocked)
	If !armed || akAggressor != player
		Return
	EndIf
	Weapon w = akSource as Weapon
	If !w || w.GetWeaponType() != 7 || target.IsEssential()
		Return
	EndIf
	armed = False
	frozen = False
	Shatter()
EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	armed = False
	If frozen
		frozen = False
		Thaw()
	EndIf
EndEvent

Function Thaw()
	IceShader.Stop(target)
	target.SetActorValue("Paralysis", 0.0)
	target.EnableAI(True)
EndFunction

Function Shatter()
	; SureAI's _00E_FrozenMEScript.ShatterEnemy
	IceShader.Stop(target)
	target.SetActorValue("Paralysis", 0.0)
	target.EnableAI(True)
	target.Kill(player)
	Utility.Wait(0.1)
	; only the frost burst (particles, no push - curator 2026-10-23: "giant logs fly out"). SureAI's other two carry
	; physics debris: Forgotten Stories' IceShatterExplosionTest.nif (6 untextured test chunks) and the NPC/draugr ice
	; gore (14 meat chunks, force 240)
	target.PlaceAtMe(ShatterExplosion02)
	target.SetCriticalStage(target.CritStage_DisintegrateStart)
	target.SetAlpha(0.0, True)
	target.AttachAshPile(ShatteredPile)
	ImpactIce.Play(target)
	Game.ShakeCamera(afStrength = 0.3)
	Utility.Wait(0.5)
	target.SetCriticalStage(target.CritStage_DisintegrateEnd)
EndFunction
