Scriptname ZP_ArgentVerdictEquipScript extends ObjectReference
{Argent Verdict (Zenderal), on the hammer: equipping it gives the player the mote ability (ZP_ArgentVerdictMotesScript,
which shows the charges on the knuckles); unequipping takes it away once the hammer is no longer in hand (checked after
a moment: a swap between two copies equips the new one first or last). The charges themselves stay (Charges) and show
again on the next equip. Until 2026-11-15 it sat on two hammers (the hand head and the spiked gauntlet; the gauntlet is
the one Argent Verdict now).}

Spell Property MoteAbility Auto
Weapon Property Hammer Auto
Actor Property PlayerRef Auto

Event OnEquipped(Actor akActor)
	If akActor && akActor == PlayerRef && MoteAbility
		akActor.AddSpell(MoteAbility, False)
	EndIf
EndEvent

Event OnUnequipped(Actor akActor)
	If !akActor || akActor != PlayerRef || !MoteAbility
		Return
	EndIf
	Utility.Wait(0.5)
	Weapon w = akActor.GetEquippedWeapon(False)
	If !w || w != Hammer
		akActor.RemoveSpell(MoteAbility)
	EndIf
EndEvent
