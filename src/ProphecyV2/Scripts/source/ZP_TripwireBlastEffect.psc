Scriptname ZP_TripwireBlastEffect extends ActiveMagicEffect
{Prophecy Tripwire: when an enemy snaps the wire, a fireball explosion goes off at their feet. Rides on Ordinator's
Tripwire Snap spell (remote-cast by the wire on whoever trips it), so Ordinator's own script is untouched. The effect's
condition limits it to actors hostile to the player; the timestamp keeps one snap from setting off several blasts when
it catches more than one actor.}

Explosion Property Blast Auto
GlobalVariable Property LastBlast Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Float now = Utility.GetCurrentRealTime()
	If now - LastBlast.GetValue() > 0.5 || now < LastBlast.GetValue()
		LastBlast.SetValue(now)
		akTarget.PlaceAtMe(Blast)
	EndIf
EndEvent
