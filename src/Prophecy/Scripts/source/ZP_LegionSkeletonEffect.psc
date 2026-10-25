Scriptname ZP_LegionSkeletonEffect extends ActiveMagicEffect
{Prophecy Necromancy - a Legion of the Damned skeleton's own ability (ActorEffect on its NPC record). The first time
it starts it stamps the game time it crumbles at into Variable07 (LifeSeconds of real time at the current TimeScale,
so a load or a new cell does not reset it); every PollSeconds it checks the clock and kills the skeleton when its time
is up. On death it leaves LegionList and fades away 3 s later (deleting the corpse takes its gear with it).
No inventory call on the dying actor: UnequipAll from OnDying crashed the game (2026-10-23, UnequipAllVisitor on a
Legion Archer that A Willing Sacrifice was disintegrating).}

FormList Property LegionList Auto
Float Property LifeSeconds = 300.0 Auto
Float Property PollSeconds = 5.0 Auto

Actor me

Event OnEffectStart(Actor akTarget, Actor akCaster)
	me = akTarget
	If me.IsDead()
		Return
	EndIf
	If me.GetActorValue("Variable07") <= 0.0
		Float timescale = (Game.GetForm(0x3A) as GlobalVariable).GetValue()     ; TimeScale
		me.SetActorValue("Variable07", Utility.GetCurrentGameTime() + LifeSeconds * timescale / 86400.0)
	EndIf
	RegisterForSingleUpdate(PollSeconds)
EndEvent

Event OnUpdate()
	If !me || me.IsDead()
		Return
	EndIf
	If Utility.GetCurrentGameTime() >= me.GetActorValue("Variable07")
		me.Kill(me)
		Return
	EndIf
	RegisterForSingleUpdate(PollSeconds)
EndEvent

Event OnDying(Actor akKiller)
	LegionList.RemoveAddedForm(me)
	Utility.Wait(3.0)
	If !me.IsDisabled()
		me.Disable(True)
	EndIf
	me.Delete()
EndEvent
