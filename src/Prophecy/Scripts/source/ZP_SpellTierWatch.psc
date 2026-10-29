Scriptname ZP_SpellTierWatch extends ActiveMagicEffect
{Prophecy Sorcery - Shatterveil's tiered spells (2026-10-28). The talent's ability: the player holds the best of Tiers
whose MinSkill their Psionics (Illusion) reaches, and none of the others. Checked when the ability starts (learning the
talent, loading a save) and every Tick seconds after, since Enderal raises skills without an event.}

Spell[] Property Tiers Auto               ; apprentice .. master
Int[] Property MinSkill Auto              ; Psionics needed for each, the first 0
String Property Skill = "Illusion" Auto   ; Psionics
Float Property Tick = 10.0 Auto

Actor player

Event OnEffectStart(Actor akTarget, Actor akCaster)
	player = akTarget
	Check(True)
	RegisterForSingleUpdate(Tick)
EndEvent

Event OnUpdate()
	If player
		Check(False)
		RegisterForSingleUpdate(Tick)
	EndIf
EndEvent

Function Check(Bool abFirst)
	Float sk = player.GetBaseActorValue(Skill)
	Int best = 0
	Int i = 1
	While i < Tiers.Length
		If sk >= MinSkill[i]
			best = i
		EndIf
		i += 1
	EndWhile
	If !player.HasSpell(Tiers[best])
		player.AddSpell(Tiers[best], False)
		If abFirst
			Debug.Notification("Spell learned: " + Tiers[best].GetName())
		Else
			Debug.Notification("Your Psionics grows: " + Tiers[best].GetName())
		EndIf
	EndIf
	i = 0
	While i < Tiers.Length
		If i != best && player.HasSpell(Tiers[i])
			player.RemoveSpell(Tiers[i])
		EndIf
		i += 1
	EndWhile
EndFunction
