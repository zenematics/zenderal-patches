Scriptname ZP_TripwireTrigger extends Tripwire
{Prophecy Gadgets - Explosive Tripwire's wire (ZP_ORD_Sne_Tripwire_Activator), in place of vanilla's Tripwire script.
The player never trips their own wire (GreaseLord 2026-11-04: "pc still ends up triggering the trap at the end of the
animation", except on uneven ground). The wire is placed 48 units in front of the kneeling player, inside its own
trigger volume's reach, and TrapTriggerBase.acceptableTrigger takes any actor: standing up after the placing scene
sends OnTriggerEnter for the player, the wire snaps on them and is spent. Only the trigger-volume path is changed;
an arrow or a swing still snaps it (OnHit), and enemies trip it as before.}

Bool Function acceptableTrigger(ObjectReference triggerRef)
	If triggerRef == Game.GetPlayer()
		Return False
	EndIf
	Return Parent.acceptableTrigger(triggerRef)
EndFunction
