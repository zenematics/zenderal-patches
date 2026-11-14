Scriptname ZET_StaggerWatchEffect extends ActiveMagicEffect
{Zenderal - Enemy Threat: the second effect of ZET_BossAbility runs only while its boss IsStaggered (a condition the
engine re-checks about once a second), so each stagger starts this once. It casts ZET_StaggerLockout: a few seconds
of an effect with Prophecy's ZP_StaggerLockout keyword, which ZET_BossPerk turns into zero poise damage (Chocolate
Poise Reforged) and which Prophecy's and EGO's stagger effects refuse. Bosses can't be stun-locked.}

Spell Property LockoutSpell Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	If akTarget && !akTarget.IsDead()
		LockoutSpell.Cast(akTarget, akTarget)
	EndIf
EndEvent
