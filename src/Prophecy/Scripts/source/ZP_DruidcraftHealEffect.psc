Scriptname ZP_DruidcraftHealEffect extends ActiveMagicEffect
{Prophecy Druid - Druidcraft's heal (2026-10-27): the second effect of our Druidcraft (Triumvirate's spell plus this).
When the target is a corpse, the caster heals the effect's magnitude in Health. NoDeathDispel on the effect, so it
starts on a dead target at all. Since 2026-10-29 the caster also gets Berries Goodberries (The Hunt spends them;
Triumvirate's Druidcraft turns the corpse to ash, so once per corpse).}

Potion Property Goodberry Auto
Int Property Berries = 1 Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	If akCaster && akTarget && akTarget.IsDead()
		akCaster.RestoreActorValue("Health", GetMagnitude())
		If Goodberry && Berries > 0
			akCaster.AddItem(Goodberry, Berries)
		EndIf
	EndIf
EndEvent
