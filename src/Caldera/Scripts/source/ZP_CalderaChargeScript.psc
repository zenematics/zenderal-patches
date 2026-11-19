Scriptname ZP_CalderaChargeScript extends ActiveMagicEffect
{Caldera (Zenderal): a charge (curator 2026-11-16: "charge enough light attacks and a power attack can trigger a
volcanic eruption"). The hammer's enchantment starts this on an enemy a light attack hits (hostile to the player, the
player not power attacking) while Charges is below Hits (its conditions): one more charge (GlobalVariable.Mod,
thread-safe; a hit that finds the count already full gives it back), and the head's cracks light one tier further
(ZP_CalderaTiersScript). The tier ability is added here too, for a hammer that was already in hand when this build was
installed (no equip event). The charge that fills it plays ChargedSound at the player (an oil fire igniting). Argent
Verdict's charge script, on Caldera's forms: a corpse never charges, the killing blow does (Fresh).}

GlobalVariable Property Charges Auto
Spell Property TierAbility Auto
Sound Property ChargedSound Auto
Actor Property PlayerRef Auto
GlobalVariable Property TimeScale Auto
Float Property FreshSeconds = 1.0 AutoReadOnly       ; a dead target counts this long after its death (the killing blow)
Int Property Tiers = 5 AutoReadOnly                  ; tools/01-build-mesh.py TIERS
Int Property Hits = 8 AutoReadOnly                   ; 02-build-records.py HITS

Event OnEffectStart(Actor akTarget, Actor akCaster)
	GlobalVariable charge = Charges
	Spell tiersAbility = TierAbility
	Actor thePlayer = PlayerRef
	Int count = Tiers
	Int full = Hits
	If !charge || !thePlayer || akCaster != thePlayer
		Return
	EndIf
	If !Fresh(akTarget, TimeScale, FreshSeconds, "ZP Caldera charge")
		Return
	EndIf
	Int now = charge.Mod(1.0) as Int
	If now > full
		charge.Mod(-1.0)
		Return
	EndIf
	If tiersAbility && !thePlayer.HasSpell(tiersAbility)
		thePlayer.AddSpell(tiersAbility, False)
	EndIf
	ZP_CalderaTiersScript.Show(thePlayer, ZP_CalderaTiersScript.Tier(now, full, count), count)
	If now == full && ChargedSound
		ChargedSound.Play(thePlayer)
	EndIf
EndEvent

; A corpse does not charge (GreaseLord 2026-11-17: "can accumulate charges by striking corpses"). The hammer's
; effects start after the hit's damage, so the killing blow's target is already dead here: a dead target counts
; only within afSeconds of its death (PO3 GetTimeOfDeath, game days, against the game clock; 0 = unknown).
Bool Function Fresh(Actor akTarget, GlobalVariable akTimeScale, Float afSeconds, String asTag) Global
	If !akTarget || !akTarget.IsDead()
		Return akTarget != None
	EndIf
	Float died = PO3_SKSEFunctions.GetTimeOfDeath(akTarget)
	Float scale = 10.0
	If akTimeScale && akTimeScale.GetValue() > 0.0
		scale = akTimeScale.GetValue()
	EndIf
	Float age = (Utility.GetCurrentGameTime() - died) * 86400.0 / scale
	Bool counts = died > 0.0 && age <= afSeconds
	Debug.Trace("[" + asTag + "] hit on dead " + akTarget + ": died " + age + " s ago, counts " + counts)
	Return counts
EndFunction
