Scriptname ZP_WhisperEquipScript extends ObjectReference
{Whisper (Zenderal), on the axe: equipping it gives the player the souls ability (ZP_WhisperSoulsScript: Entropy spells
feed it souls, its glow shows them); unequipping takes it away once the axe is in neither hand (checked after a moment:
a swap between hands or two copies equips the new one first or last). The souls themselves stay (Souls) and show again
on the next equip. Argent Verdict's equip script, both hands (Whisper is one-handed).}

Spell Property SoulsAbility Auto
Weapon Property Axe Auto
Actor Property PlayerRef Auto

Event OnEquipped(Actor akActor)
	If akActor && akActor == PlayerRef && SoulsAbility
		akActor.AddSpell(SoulsAbility, False)
	EndIf
EndEvent

Event OnUnequipped(Actor akActor)
	If !akActor || akActor != PlayerRef || !SoulsAbility
		Return
	EndIf
	Utility.Wait(0.5)
	If akActor.GetEquippedWeapon(False) != Axe && akActor.GetEquippedWeapon(True) != Axe
		akActor.RemoveSpell(SoulsAbility)
	EndIf
EndEvent
