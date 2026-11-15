Scriptname ZP_ArgentVerdictChargeScript extends ActiveMagicEffect
{Argent Verdict (Zenderal): a charge (curator 2026-11-14: "lets have it build charges", "very small motes of light
that light up on each of the knuckles"; 2026-11-15: "make the charge up be 8 light attacks not 4"). The hammer's
enchantment starts this on an enemy a light attack hits (hostile to the player, the player not power attacking) while
Charges is below Hits (its conditions): one more charge (GlobalVariable.Mod, thread-safe; a hit that finds the count
already full gives it back), and every Hits / Knuckles charges one more mote lit (ZP_ArgentVerdictMotesScript.Show,
Lit). The mote ability is added here too, for a hammer that was already in hand when this build was installed (no
equip event). The charge that fills the last knuckle rings ChargedSound at the player (curator 2026-11-14: "add this
sound once the weapon is full charged ready to release its payload": the curator's church bell, tools/03 --charged).}

GlobalVariable Property Charges Auto
Spell Property MoteAbility Auto
Sound Property ChargedSound Auto
Actor Property PlayerRef Auto
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
