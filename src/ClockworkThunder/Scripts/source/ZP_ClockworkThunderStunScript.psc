Scriptname ZP_ClockworkThunderStunScript extends ActiveMagicEffect
{Clockwork Thunder (Zenderal): the chain lightning stuns what it strikes, but only enemies below the player's
level. Runs on every actor the chain lightning reaches (an effect of the chain spell itself); casts StunSpell
(a few seconds of paralysis with the shock shader) from the player at it. A condition cannot compare the
target's level with the player's, hence the script.}

Spell Property StunSpell Auto
Actor Property PlayerRef Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	If !akTarget || akTarget == PlayerRef || akTarget.IsDead() || akTarget.IsPlayerTeammate()
		Return
	EndIf
	If akTarget.GetLevel() < PlayerRef.GetLevel()
		StunSpell.Cast(PlayerRef, akTarget)
	EndIf
EndEvent
