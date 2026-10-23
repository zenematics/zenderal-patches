Scriptname ZP_PlaySoundEffect extends ActiveMagicEffect
{Plays one sound on the effect's target when it starts - adds a sound to a power without touching the power's own
scripts (Explosive Tripwire's ratchet).}

Sound Property SoundToPlay Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	SoundToPlay.Play(akTarget)
EndEvent
