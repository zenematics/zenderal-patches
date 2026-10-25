Scriptname ZEN_TR_PoolPenaltyEffect extends ActiveMagicEffect
{Zenderal Traits - a trait's percentage cut to a maximum pool (curator 2026-10-25: the cut should apply to every
increase, not once). It keeps Penalty - an ability whose one effect lowers PoolName, magnitude set here - at Fraction
of the pool's maximum counted without the cut itself, so level-ups, gear, potions and buffs are all cut too. SKSE's
GetActorValueMax is the maximum with every buff and debuff, so the uncut maximum is that plus the cut already applied.
Checked every PollSeconds; when the cut should change by a point or more, the ability is re-added with the new
magnitude (Spell.SetNthEffectMagnitude). Removing and re-adding a Recover value modifier moves the current value with
the maximum, so a refresh never heals. Zen Traits' Aeterna Veins cuts Health the same way, sized by a perk entry and
refreshed on level-up only.}

Spell Property Penalty Auto
String Property PoolName = "Health" Auto
Float Property Fraction = 0.15 Auto
Float Property PollSeconds = 5.0 Auto

Actor target
Float applied
Bool finished

Event OnEffectStart(Actor akTarget, Actor akCaster)
	target = akTarget
	Refresh()
	RegisterForSingleUpdate(PollSeconds)
EndEvent

Event OnUpdate()
	If finished || !target
		Return
	EndIf
	Refresh()
	RegisterForSingleUpdate(PollSeconds)
EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	finished = True
	akTarget.RemoveSpell(Penalty)
EndEvent

Function Refresh()
	Float uncut = target.GetActorValueMax(PoolName) + applied
	Float want = Math.Floor(uncut * Fraction + 0.5)
	If Math.Abs(want - applied) < 1.0
		Return
	EndIf
	target.RemoveSpell(Penalty)
	Penalty.SetNthEffectMagnitude(0, want)
	target.AddSpell(Penalty, False)
	applied = want
EndFunction
