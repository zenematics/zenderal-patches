Scriptname ZP_RiseArmorPierceScript extends ObjectReference
{Rise (Zenderal - Sting and Rise): gives the player ArmorPiercePerk the first time they equip Rise. The perk
(Mod Target Damage Resistance x0) only applies to hits from a weapon with Rise's keyword on a target that still
has Sting's venom, so it is never taken away. A script because SPID never distributes to the player and a
weapon enchantment only reaches the enemy it strikes.}

Perk Property ArmorPiercePerk Auto
Actor Property PlayerRef Auto

Event OnEquipped(Actor akActor)
	If akActor == PlayerRef && !PlayerRef.HasPerk(ArmorPiercePerk)
		PlayerRef.AddPerk(ArmorPiercePerk)
	EndIf
EndEvent
