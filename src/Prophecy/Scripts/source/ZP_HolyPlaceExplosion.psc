Scriptname ZP_HolyPlaceExplosion extends ActiveMagicEffect
{Prophecy - Holy Templar Magic. Stands in for vanilla Skyrim's magicPlaceExplosionScript, which Enderal does not ship:
places ExplosionRef on the effect's target when the effect starts. Used by Wrath of the Heavens' sky-bolts (the explosion
places the bolt activator) and by Consecrate Dead / Sanctuary's particle bursts. The property keeps the vanilla name, so
the copied records' VMAD values carry over unchanged.}

Explosion Property ExplosionRef Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	If ExplosionRef && akTarget
		akTarget.PlaceAtMe(ExplosionRef)
	EndIf
EndEvent
