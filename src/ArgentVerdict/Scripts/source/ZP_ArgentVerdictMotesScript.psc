Scriptname ZP_ArgentVerdictMotesScript extends ActiveMagicEffect
{Argent Verdict (Zenderal): the knuckle motes (curator 2026-11-14: "very small motes of light that light up on each of
the knuckles"). The hammer's meshes carry four nodes ZP_ArgentMote1..4 (tools/motes.py: Kittytail's Absolution rune
circle, very small, one over each knuckle) at scale 0. A mote is lit by setting its node's scale to 1 (SKSE
NetImmerse.SetNodeScale) in both views; Charges (0..Hits) says how many: one per Hits / Knuckles charges (Lit), so the
last one lights exactly when the charge is full (since 2026-11-15 a full charge is 8 light-attack hits, two a mote).
This ability (added while a hammer is equipped, ZP_ArgentVerdictEquipScript; and by the first charge, for a hammer
already in hand) sets them on start and again every Poll seconds: a weapon's 3D is rebuilt with its nodes at scale 0
on every equip, load and race change. Show() and Lit() are Global, so the charge and release scripts light and clear
them at once.}

GlobalVariable Property Charges Auto
Float Property Poll = 1.0 AutoReadOnly
Int Property Knuckles = 4 AutoReadOnly               ; 02-build-records.py KNUCKLES
Int Property Hits = 8 AutoReadOnly                   ; 02-build-records.py HITS

Event OnEffectStart(Actor akTarget, Actor akCaster)
	If Charges && akTarget
		Show(akTarget, Lit(Charges.GetValueInt(), Hits, Knuckles), Knuckles)
		RegisterForSingleUpdate(Poll)
	EndIf
EndEvent

Event OnUpdate()
	Actor a = GetTargetActor()
	If Charges && a
		Show(a, Lit(Charges.GetValueInt(), Hits, Knuckles), Knuckles)
		RegisterForSingleUpdate(Poll)
	EndIf
EndEvent

; The motes aiCharges of aiFull charges light: whole steps only, so all aiCount are lit only at a full charge.
Int Function Lit(Int aiCharges, Int aiFull, Int aiCount) Global
	If aiFull <= 0 || aiCharges <= 0
		Return 0
	EndIf
	If aiCharges >= aiFull
		Return aiCount
	EndIf
	Return aiCharges * aiCount / aiFull
EndFunction

; Motes 1..aiLit at scale 1, the rest at 0, in the third- and first-person 3D.
Function Show(Actor akActor, Int aiLit, Int aiCount) Global
	Int i = 1
	While i <= aiCount
		Float s = 0.0
		If i <= aiLit
			s = 1.0
		EndIf
		String node = "ZP_ArgentMote" + i
		NetImmerse.SetNodeScale(akActor, node, s, False)
		NetImmerse.SetNodeScale(akActor, node, s, True)
		i += 1
	EndWhile
EndFunction
