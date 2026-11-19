Scriptname ZP_OwlBowFreezeEffect extends ActiveMagicEffect
{Owl Bow (Zenderal): an ice arrow froze its target solid (the enchantment's 5% roll is the effect's
GetRandomPercent condition). Weak enemies only, Ice Shot's rule (curator 2026-10-29: the freeze is too strong on
bosses): no higher level than the player, never a unique actor, never a follower or a MagicNoFreeze creature.
The freeze is Ice Shot's (SureAI's _00E_FrozenMEScript: AI off, Paralysis 1) with Enderal's frozen look and
Arctic Wind's freeze sound, for the effect's duration; no shatter.}

Keyword Property MagicNoFreeze Auto
EffectShader Property IceShader Auto          ; FrostIceFormFXShader02 0DC20E - _00E_Frozen_ME's look
Sound Property FreezeSound Auto               ; _00E_A1_ArcticWindFreezeM

Actor target
Bool frozen

Event OnEffectStart(Actor akTarget, Actor akCaster)
	target = akTarget
	Actor player = Game.GetPlayer()
	If !target || target.IsDead() || target.HasKeyword(MagicNoFreeze) || target.IsPlayerTeammate() || target == player
		Return
	EndIf
	If target.GetLevel() > player.GetLevel() || target.GetLeveledActorBase().IsUnique()
		Return
	EndIf
	frozen = True
	FreezeSound.Play(target)
	IceShader.Play(target)
	target.EnableAI(False)
	target.SetActorValue("Paralysis", 1.0)
EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	If frozen
		frozen = False
		IceShader.Stop(target)
		target.SetActorValue("Paralysis", 0.0)
		target.EnableAI(True)
	EndIf
EndEvent
