Scriptname _00E_ArkanistenfieberBlitzheilungSCN extends activemagiceffect
{Zen Traits' version (Shazdeh, MIT), forked by Zenderal - Zen Traits Fixes. Lines marked ; ZP.
Enderal 2.1 made the potion fever effect (_00E_AlchIncreaseArcaneFever 02F21D) a value modifier on LastFlattered:
the engine adds the fever and SureAI's script only shows the message. Zen Traits' script is from 2.0, when the effect
was Type: Script, so on 2.1 it added the fever a second time. Now, on a LastFlattered value modifier, it only adds what
Zen Traits' traits change on top and shows the "increased" message; on every other effect (EGO's script-type and
Health/Mana/Stamina fever effects) it does what Zen Traits did.}

Import ArcaneFever

float skseMagnitude
bool bEngineApplied ; ZP

event OnInit()
    skseMagnitude = GetMagnitude()
    MagicEffect base = GetBaseObject() ; ZP
    bEngineApplied = base && PO3_SKSEFunctions.GetPrimaryActorValue(base) == "LastFlattered" ; ZP
endevent

Event OnEffectFinish(Actor akTarget, Actor akCaster)

	if akTarget != PlayerREF
		return
	endif

	If bEngineApplied ; ZP
		TraitsOnTop(Math.Abs(skseMagnitude)) ; ZP
	Else ; ZP
		ArcaneFever.ModFever(-skseMagnitude, bVisuals)
	EndIf ; ZP

EndEvent

; ZP: the engine already added afMagnitude (with Mental Expert, which 2.1 handles through its own effect variant).
; Add only Zen Traits' trait multipliers on top, then show Zen Traits' "increased" message for the whole amount.
Function TraitsOnTop(Float afMagnitude)
	ZenTraits_ArcaneFeverScript zt = ArcaneFever.GetScript()
	If !zt || afMagnitude <= 0.0
		Return
	EndIf
	Float total = -zt.ApplyIncreaseFeverMods(-afMagnitude)
	Perk mentalExpert = Game.GetFormFromFile(0x069D07, "Skyrim.esm") as Perk   ; _00E_Class_Thaumaturge_P07_MentalExpert
	If mentalExpert && PlayerREF.HasPerk(mentalExpert)
		total = total / 0.67
	EndIf
	Float extra = total - afMagnitude
	If extra != 0.0
		PlayerREF.ModActorValue("LastFlattered", -extra)
	EndIf
	zt.Notify(-total, 0.0, bVisuals)
EndFunction

bool Property bVisuals = false Auto

Actor Property PlayerREF Auto
