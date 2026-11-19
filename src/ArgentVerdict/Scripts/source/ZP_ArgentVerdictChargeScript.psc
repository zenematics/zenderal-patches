Scriptname ZP_ArgentVerdictChargeScript extends ActiveMagicEffect
{Argent Verdict (Zenderal): a charge (curator 2026-11-14: "lets have it build charges", "very small motes of light
that light up on each of the knuckles"; 2026-11-15: "make the charge up be 8 light attacks not 4"). The hammer's
enchantment starts this on an enemy a light attack hits (hostile to the player, the player not power attacking) while
Charges is below Hits (its conditions): one more charge (GlobalVariable.Mod, thread-safe; a hit that finds the count
already full gives it back), and every Hits / Knuckles charges one more mote lit (ZP_ArgentVerdictMotesScript.Show,
Lit). The mote ability is added here too, for a hammer that was already in hand when this build was installed (no
equip event). The charge that fills the last knuckle rings ChargedSound at the player (curator 2026-11-14: "add this
sound once the weapon is full charged ready to release its payload": the curator's church bell, tools/03 --charged).
A corpse never charges; the killing blow does (Fresh).}

GlobalVariable Property Charges Auto
Spell Property MoteAbility Auto
Sound Property ChargedSound Auto
Actor Property PlayerRef Auto
GlobalVariable Property TimeScale Auto
Float Property FreshSeconds = 1.0 AutoReadOnly       ; a dead target counts this long after its death (the killing blow)
Int Property Knuckles = 4 AutoReadOnly               ; the motes (02-build-records.py KNUCKLES)
Int Property Hits = 8 AutoReadOnly                   ; the light-attack hits a full charge takes (02-build-records.py HITS)

Event OnEffectStart(Actor akTarget, Actor akCaster)
	GlobalVariable charge = Charges
	Spell motes = MoteAbility
	Actor thePlayer = PlayerRef
	Int count = Knuckles
	Int full = Hits
	If !charge || !thePlayer || akCaster != thePlayer
		Return
	EndIf
	If !Fresh(akTarget, TimeScale, FreshSeconds, "ZP Argent charge")
		Return
	EndIf
	Int now = charge.Mod(1.0) as Int
	If now > full
		charge.Mod(-1.0)
		Return
	EndIf
	If motes && !thePlayer.HasSpell(motes)
		thePlayer.AddSpell(motes, False)
	EndIf
	ZP_ArgentVerdictMotesScript.Show(thePlayer, ZP_ArgentVerdictMotesScript.Lit(now, full, count), count)
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
