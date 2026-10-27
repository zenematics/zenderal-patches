Scriptname ZP_WrathGate extends ActiveMagicEffect
{Prophecy Faith - Wrath of the Lightborn's cast (2026-10-25). Checks Arcane Fever once, when the spell is cast: at
MaxFever or more it refuses (its own fever would reach 100%, which kills); otherwise it casts the real cloak
(CloakSpell, 60 s of sky-bolts) and the fever cost (FeverSpell, Enderal's _00E_IncreaseArcaneFeverFFSelf). The first
version gated every effect with a fever condition, which the engine re-checks while the effect runs, so the cast's own
fever ended the cloak after one volley. Arcane Fever is stored negated in LastFlattered.}

Spell Property CloakSpell Auto
Spell Property FeverSpell Auto
Float Property MaxFever = 50.0 Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Actor who = akCaster
	If !who
		who = akTarget
	EndIf
	If !who || !CloakSpell
		Return
	EndIf
	If -who.GetActorValue("LastFlattered") >= MaxFever
		If who == Game.GetPlayer()
			Debug.Notification("Your Arcane Fever is too high to call down the Wrath of the Lightborn.")
		EndIf
		Return
	EndIf
	CloakSpell.Cast(who, who)
	If FeverSpell
		FeverSpell.Cast(who, who)
	EndIf
EndEvent
