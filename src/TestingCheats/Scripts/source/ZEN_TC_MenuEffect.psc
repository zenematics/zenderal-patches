Scriptname ZEN_TC_MenuEffect extends ActiveMagicEffect
{Testing Cheats - the lesser power's menu. Gain levels / add experience go through Enderal's own
_00E_EPUpdateFunctions.receiveEP on the player, so every level is a real Enderal level-up (stat choice, 1 talent
point, 5 learning points, 4 crafting points), handed out once menus are closed and the player is out of combat.
"Gain levels" asks _00E_Func_ComputeNeededExp for the total EP of the target level, with the live EXPMult and
EXPMultSlope (EGO sets EXPMult 450). Sliders are B612's QuantitySlider. It remembers its last pick and may return it
on Cancel, so every action ends with a confirmation box. Prophecy points are looked up by file, so the mod works
without Prophecy installed.}

Message Property MenuMessage Auto
Message Property ConfirmMessage Auto      ; "Apply %.0f?" - Apply / Cancel
GlobalVariable Property PlayerExp Auto
GlobalVariable Property PlayerLevel Auto
GlobalVariable Property EXPMult Auto
GlobalVariable Property EXPMultSlope Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Int choice = MenuMessage.Show()
	If choice == 0
		Int n = Pick("Levels to gain", 1, 60)
		If n > 0
			GainLevels(n)
		EndIf
	ElseIf choice == 1
		Int k = Pick("Experience to add (thousands)", 1, 500)
		If k > 0
			GiveEP(k * 1000)
		EndIf
	ElseIf choice == 2
		GlobalVariable points = Game.GetFormFromFile(0x802, "Zenderal - Prophecy.esp") as GlobalVariable   ; ZP_ProphecyPoints
		If !points
			Debug.Notification("Prophecy is not installed.")
			Return
		EndIf
		Int p = Pick("Prophecy points to add", 1, 30)
		If p > 0
			points.Mod(p)
			Debug.Notification("Prophecy points: " + points.GetValueInt())
		EndIf
	EndIf
EndEvent

; Slider, then a confirmation of the picked number. 0 = cancelled.
Int Function Pick(String asTitle, Int aiMin, Int aiMax)
	b612_QuantitySlider slider = b612.GetQuantitySlider()
	If !slider
		Debug.Notification("Testing Cheats needs B612 (b612.esp).")
		Return 0
	EndIf
	Int value = slider.Show(asTitle, aiMin, aiMax)
	If value < aiMin || value > aiMax
		Return 0
	EndIf
	If ConfirmMessage.Show(value) != 0
		Return 0
	EndIf
	Return value
EndFunction

Function GainLevels(Int aiLevels)
	Int target = PlayerLevel.GetValueInt() + aiLevels
	; total EP needed to reach `target` = the "needed" value of the level below it
	Float need = _00E_Func_ComputeNeededExp.Run(target - 1, EXPMultSlope.GetValue(), EXPMult.GetValue())
	Int amount = (need - PlayerExp.GetValue()) as Int + 1
	If amount <= 0
		Debug.Notification("You already have the experience for level " + target + ".")
		Return
	EndIf
	GiveEP(amount)
EndFunction

Function GiveEP(Int aiAmount)
	_00E_EPUpdateFunctions ep = Game.GetPlayer() as _00E_EPUpdateFunctions
	If !ep
		Debug.Notification("Enderal's level system script is not on the player.")
		Return
	EndIf
	ep.receiveEP(aiAmount)
	Debug.Notification("Level-ups follow once you are out of combat with no menu open.")
EndFunction
