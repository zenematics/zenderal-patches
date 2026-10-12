Scriptname _00E_AmbrosiaEffect extends activemagiceffect

; ============================================================================
; Zenderal - Zen Traits Fixes
;
; Shazdeh's Zen Traits _00e_ambrosiaeffect.psc (upstream main @ 1ae67a8) with
; ONE change, marked "; ZP". Everything else is their original. Credit:
; Shazdeh (Zen Traits, MIT) and SureAI (the script it replaces).
;
; Upstream read the magnitude from the Variable08 actor value, which nothing in
; Enderal or the list ever writes, so it was always 0 and Ambrosia reduced
; Arcane Fever by 0 while still playing the flash, sound and notification.
; The magnitude lives on the ALCH effect item (_00E_Ambrosia 0FEC69 ->
; _00E_AlchReduceArcaneFever 1037EC: 20 in base Enderal, 15 under EGO), which
; is where SureAI's own copy reads it. See shazdeh/Zen-Traits#2.
; ============================================================================

Event OnEffectStart(Actor akTarget, Actor akCaster)
	float fMagnitude = Self.GetMagnitude() ; ZP - was: -akTarget.GetActorValue("Variable08") + RestoreActorValue

	if akTarget != Game.GetForm(0x14)
		return
	endif

	fMagnitude = ArcaneFever.GetAmbrosiaMod(fMagnitude)
	ArcaneFever.ModFever(fMagnitude, True)
EndEvent
