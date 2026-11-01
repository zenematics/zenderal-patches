Scriptname ZP_PlaySoundEffect extends ActiveMagicEffect
{Plays one sound on the effect's target when it starts - adds a sound to a power without touching the power's own
scripts (Explosive Tripwire's ratchet). PlayOnCaster plays it on the caster instead (Deadeye's shot, carried by a
hit spell whose target is the enemy).}

Sound Property SoundToPlay Auto
Bool Property PlayOnCaster = False Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	If PlayOnCaster && akCaster
		SoundToPlay.Play(akCaster)
	Else
		SoundToPlay.Play(akTarget)
	EndIf
EndEvent
