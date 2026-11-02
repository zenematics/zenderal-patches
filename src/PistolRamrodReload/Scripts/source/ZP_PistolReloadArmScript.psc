Scriptname ZP_PistolReloadArmScript extends ReferenceAlias
{Zenderal - Pistol Ramrod Reload. With a pistol (a staff) in the left hand and the right hand empty, the third-person
graph takes the right arm from the free hand's one-handed idle while the left hand casts (1hm_behavior,
MLh_1HM_Idle_Blend), so the reload clip could not move the right forearm or hand (ZenBoneTrace, 2026-11-01). The
Pandora patch zpistolreload binds that idle's weight to the graph variable fZenPistolRightArmIdle (default 1.0). This
sets it to 0 when the reload clip plays (a left-hand pistol's reload, right hand empty: the OAR submods' own
conditions) and back to 1 RESET_AFTER later, by which time the clip has returned the arm to the idle's pose. A
right-hand pistol with the left hand empty is the same, mirrored: 0_master's H2H_MRh idle gives the left arm to the
idle, and fZenPistolLeftArmIdle frees it.
Two pistols (2026-11-02): the magic graph's DualStaff_Blend gives the other arm to the other gun's own graph. The patch
wraps it in a blend on fZenPistolDualReload (default 0): -1 for a left-hand reload and +1 for a right-hand one hand
the whole body to the reloading gun's clip, which tucks the other gun in the belt, loads, and draws it back; reset to 0
DUAL_RESET_AFTER later, while the clip holds its last pose (both guns on Loop's idles). Mod event ZP_FlintlockHolster
(the Flintlock Overhaul's ammo script owns the charge) keeps the tucked gun from firing for DUAL_LOCK seconds.
A reload plays only when asked for (2026-11-02, curator: a shot must leave the other hand free): a shot is Loop's shot
alone; pressing fire on the empty gun (the Flintlock Overhaul's mod event ZP_PistolDryReload) starts the reload's cast
with the hand's request variable (REQUEST_L / R, the Pandora patch's) at 1, which every reload clip's OAR conditions
require. The clips start from the hold (tools/01 TRIM), so the arms are handed over as the clip starts, and back at once
when the reload is cut short (HoldReload). A reload cut short leaves the gun empty, and the next press asks again.
A one-handed melee weapon in the other hand (2026-11-02): the clip sheathes it on the two-pistol timeline. Pistol left:
the right arm is 1hm_behavior's, as for an empty hand (ARM_VARIABLE). Pistol right: 0_master's MRh_1HM idle and the
root's grip override hold the left arm and weapon, which the patch hands over with STOW_VARIABLE (default 1). The
arm's idle there is whatever moveset wins, so both fade over FADE_STEPS instead of switching.
Prophecy's Hair Trigger (2026-11-02, curator: with it no reload was needed, the guns spammed): its reloads play tools/07's
twins of the clips, HAIR_TRIGGER_SPEED faster, so every time here is that much shorter with the perk (Pace).
Pistols are recognised by Loop's keyword (KID gives it to the Gentleman's pistols; Reversal Shadow carries it), Hair
Trigger by Prophecy's perk; both looked up by FormID, so this plugin masters neither.}

Actor Property PlayerRef Auto
String Property ARM_VARIABLE = "fZenPistolRightArmIdle" AutoReadOnly    ; pistol left: the free right arm (1hm_behavior)
String Property LEFT_ARM_VARIABLE = "fZenPistolLeftArmIdle" AutoReadOnly ; pistol right: the free left arm (0_master)
String Property DUAL_VARIABLE = "fZenPistolDualReload" AutoReadOnly     ; two pistols: -1 left gun's clip, +1 right's
String Property STOW_VARIABLE = "fZenPistolLeftStow" AutoReadOnly       ; pistol right, melee weapon left (0_master)
String Property REQUEST_L = "fZenPistolReloadL" AutoReadOnly   ; reload asked for: 1 while its clip starts (OAR)
String Property REQUEST_R = "fZenPistolReloadR" AutoReadOnly
Float Property REQUEST_HOLD = 0.4 AutoReadOnly     ; the request stays 1 this long after the release (its clip has started)
Int Property FADE_STEPS = 6 AutoReadOnly       ; a free arm fades over this many variable sets, one a frame or so
; times from the hand-over, right after the release: the reload clip's start (it starts from the hold: tools/01 TRIM)
Float Property RESET_WANT_AFTER = 0.05 AutoReadOnly   ; bWantCast back to false this long after the release (OnUpdate)
Float Property RESET_AFTER = 1.8 AutoReadOnly   ; the 2.1 s clip: the arm is at rest from ~1.85 s
; the two-pistol clip (tools/01 DUAL_*, TRIM earlier): its last pose from 2.86 s, ends 3.39 s; 2.95 s after the
; hand-over is clip time ~3.0, in that hold
Float Property DUAL_RESET_AFTER = 2.95 AutoReadOnly
Float Property DUAL_LOCK = 2.95 AutoReadOnly    ; the other gun cannot fire until the body is handed back
String Property LoopPlugin = "Pistol animation by Loop.esp" AutoReadOnly
Int Property LOOP_KEYWORD_ID = 0x801 AutoReadOnly   ; Pistol_Animation_By_Loop
String Property ProphecyPlugin = "Zenderal - Prophecy.esp" AutoReadOnly
Int Property HAIR_TRIGGER_ID = 0xB12 AutoReadOnly   ; ZP_Prophecy_HairTrigger: its reloads play faster clips
Float Property HAIR_TRIGGER_SPEED = 1.75 AutoReadOnly  ; tools/07 SPEED: the 2.11 s reload in 1.2 s (the talent's text)
Int Property LEFT_HAND = 0 AutoReadOnly              ; the Flintlock script's hand / GetEquippedItemType hand
Int Property RIGHT_HAND = 1 AutoReadOnly
Int Property TYPE_STAFF = 8 AutoReadOnly             ; GetEquippedItemType

Keyword pistolKeyword
Perk hairTrigger
Int shots       ; the newest shot owns the reset, per hand
Int shotsRight
Int shotsDual
String resetSide      ; OnUpdate's: the request it clears after the release
String resetRequest

Event OnInit()
	Setup()
EndEvent

Event OnPlayerLoadGame()
	Setup()
EndEvent

Function Setup()
	UnregisterForActorAction(2)    ; the first builds handed the arms over at the shot's spell-fire (saves keep it)
	RegisterForModEvent("ZP_PistolDryReload", "OnDryReload")
	pistolKeyword = None
	hairTrigger = None
	If Game.GetModByName(LoopPlugin) != 255
		pistolKeyword = Game.GetFormFromFile(LOOP_KEYWORD_ID, LoopPlugin) as Keyword
	EndIf
	If Game.GetModByName(ProphecyPlugin) != 255
		hairTrigger = Game.GetFormFromFile(HAIR_TRIGGER_ID, ProphecyPlugin) as Perk
	EndIf
	PlayerRef.SetAnimationVariableFloat(ARM_VARIABLE, 1.0)
	PlayerRef.SetAnimationVariableFloat(LEFT_ARM_VARIABLE, 1.0)
	PlayerRef.SetAnimationVariableFloat(DUAL_VARIABLE, 0.0)
	PlayerRef.SetAnimationVariableFloat(STOW_VARIABLE, 1.0)
	PlayerRef.SetAnimationVariableFloat(REQUEST_L, 0.0)
	PlayerRef.SetAnimationVariableFloat(REQUEST_R, 0.0)
EndFunction

; The Flintlock Overhaul's ammo script: fire pressed on that hand's empty gun. The reload clip plays the shot's release
; state without a shot, started the engine's way (traced 2026-11-02: the engine never sends the cast events by name):
; bWantCast<side> set true, which the magic graph's BeginCast_OnFalseToTrueMod turns into BeginCast<side>
; (MagicRootBehavior -> CastingState), and the event of Skyrim.esm's idle Cast<side>FireForgetAimed (013467 for the
; left), M?h_SpellAimedStart (-> the aimed cast: NotCasting false; BeginCastLeft sent alone left again at once, through
; CastStop_EventOnFalseToTrueMod). The right hand's aimed cast takes its release from its ready state only
; (MRh_AimedFireAndForgetBehavior: MRh_SpellRelease_Event from MRh_AimedReadyState, reached by the wildcard
; MRh_SpellReady_Event; the left one's release is itself a wildcard), so MRh_SpellReady_Event first: without it the
; right gun stayed in its charge pose, no reload (traced 2026-11-02). No wait between them: the precharge showed the gun
; raised to aim. The release clip ends on M?h_Equipped_Event; its M?h_SpellFire_Event finds the gun at 0 charge (no
; projectile, traced). The request variable is 1 while the clip starts (OAR); bWantCast<side> goes back to false, as the
; engine leaves it after a cast, or the next real cast's false -> true edge (its BeginCast) would never come. The arms
; are handed over as the clip starts.
Event OnDryReload(String eventName, String strArg, Float numArg, Form sender)
	Int slot = strArg as Int
	If slot < LEFT_HAND || slot > RIGHT_HAND || !pistolKeyword
		Return
	EndIf
	Weapon pistol = PlayerRef.GetEquippedWeapon(slot == LEFT_HAND)
	If !pistol || !pistol.HasKeyword(pistolKeyword)
		Return
	EndIf
	Debug.Trace("[ZP PistolReload] reload asked for, hand " + slot + ": cast started by bWantCast, released by graph event")
	String side = "Left"
	String prefix = "MLh_"
	String request = REQUEST_L
	If slot == RIGHT_HAND
		side = "Right"
		prefix = "MRh_"
		request = REQUEST_R
	EndIf
	PlayerRef.SetAnimationVariableFloat(request, 1.0)
	PlayerRef.SetAnimationVariableBool("bWantCast" + side, True)
	Debug.SendAnimationEvent(PlayerRef, prefix + "SpellAimedStart")
	If slot == RIGHT_HAND
		Debug.SendAnimationEvent(PlayerRef, prefix + "SpellReady_Event")
	EndIf
	Debug.SendAnimationEvent(PlayerRef, prefix + "SpellRelease_Event")
	resetSide = side
	resetRequest = request
	RegisterForSingleUpdate(RESET_WANT_AFTER)
	If PlayerRef.GetAnimationVariableBool(Casting(slot))   ; the arms as the clip starts; none for a refused cast
		HandleReload(slot, 1 - slot)
	EndIf
EndEvent

; After a request's release: bWantCast<side> back to false, and the request REQUEST_HOLD later (its clip has started)
Event OnUpdate()
	String side = resetSide
	String request = resetRequest
	PlayerRef.SetAnimationVariableBool("bWantCast" + side, False)
	Utility.Wait(REQUEST_HOLD)
	PlayerRef.SetAnimationVariableFloat(request, 0.0)
EndEvent

String Function Casting(Int slot)
	If slot == LEFT_HAND
		Return "IsCastingLeft"
	EndIf
	Return "IsCastingRight"
EndFunction

; how much of each time a reload takes: 1, or less with Hair Trigger (its clips play HAIR_TRIGGER_SPEED faster)
Float Function Pace()
	If hairTrigger && PlayerRef.HasPerk(hairTrigger)
		Return 1.0 / HAIR_TRIGGER_SPEED
	EndIf
	Return 1.0
EndFunction

; `seconds` while that hand's reload plays: a cut-short reload (an attack, the other hand) ends it, so the arms come
; back at once
Function HoldReload(Int slot, Float seconds)
	Float until = Utility.GetCurrentRealTime() + seconds
	String casting = Casting(slot)
	While Utility.GetCurrentRealTime() < until && PlayerRef.GetAnimationVariableBool(casting)
		Utility.Wait(0.1)
	EndWhile
EndFunction

; The arms for the reload the shot clip plays, by what the other hand holds (its OAR submods' conditions)
Function HandleReload(Int slot, Int other)
	Int otherType = PlayerRef.GetEquippedItemType(other)
	If otherType == TYPE_STAFF
		Weapon otherGun = PlayerRef.GetEquippedWeapon(other == LEFT_HAND)
		If otherGun && otherGun.HasKeyword(pistolKeyword)
			DualReload(slot, other)
		EndIf
		Return
	ElseIf otherType >= 1 && otherType <= 4     ; sword, dagger, axe, mace: sheathed for the reload
		StowReload(slot)
		Return
	ElseIf otherType != 0
		Return
	EndIf
	If slot == LEFT_HAND
		shots += 1
		Int mine = shots
		PlayerRef.SetAnimationVariableFloat(ARM_VARIABLE, 0.0)
		HoldReload(slot, RESET_AFTER * Pace())
		If mine == shots
			PlayerRef.SetAnimationVariableFloat(ARM_VARIABLE, 1.0)
		EndIf
	Else
		shotsRight += 1
		Int mineRight = shotsRight
		PlayerRef.SetAnimationVariableFloat(LEFT_ARM_VARIABLE, 0.0)
		HoldReload(slot, RESET_AFTER * Pace())
		If mineRight == shotsRight
			PlayerRef.SetAnimationVariableFloat(LEFT_ARM_VARIABLE, 1.0)
		EndIf
	EndIf
EndFunction

; A melee weapon in the other hand: that arm fades to the clip, which sheathes the weapon, reloads and draws it again
; (the two-pistol timeline: handed back DUAL_RESET_AFTER after the shot, while the clip holds its last pose)
Function StowReload(Int slot)
	If slot == LEFT_HAND
		shots += 1
		Int mine = shots
		FadeOut(ARM_VARIABLE, True)
		HoldReload(slot, DUAL_RESET_AFTER * Pace())
		If mine == shots
			FadeIn(ARM_VARIABLE, True)
		EndIf
	Else
		shotsRight += 1
		Int mineRight = shotsRight
		FadeOut(STOW_VARIABLE, False)
		HoldReload(slot, DUAL_RESET_AFTER * Pace())
		If mineRight == shotsRight
			FadeIn(STOW_VARIABLE, False)
		EndIf
	EndIf
EndFunction

; A free arm's variable from 1 to 0 over FADE_STEPS sets, one after the other with no wait (each Papyrus call takes a
; frame or so): the clip's share of the arm rises evenly. Four sets 0.03 s apart took ~4 frames each in game, and
; the reload clip, which starts from the hold (tools/01 TRIM), had moved the hand on by then: it stepped 12-15 units
; at a time (traced 2026-11-02). `share`: the idle's weight in a blend against the clip's RIGHT_ARM_EPSILON (0.01,
; tools/03), whose share of the arm is 0.01 / (x + 0.01), so x = 0.01 (1 - s) / s for a share s. Otherwise a
; parametric blend (linear).
Function FadeOut(String var, Bool share)
	Int i = 1
	While i < FADE_STEPS
		PlayerRef.SetAnimationVariableFloat(var, ArmWeight(i as Float / FADE_STEPS, share))
		i += 1
	EndWhile
	PlayerRef.SetAnimationVariableFloat(var, 0.0)
EndFunction

Function FadeIn(String var, Bool share)
	Int i = FADE_STEPS - 1
	While i > 0
		PlayerRef.SetAnimationVariableFloat(var, ArmWeight(i as Float / FADE_STEPS, share))
		i -= 1
	EndWhile
	PlayerRef.SetAnimationVariableFloat(var, 1.0)
EndFunction

; the free arm's variable for the clip's share s of the arm (0 < s < 1)
Float Function ArmWeight(Float s, Bool share)
	If share
		Return 0.01 * (1.0 - s) / s
	EndIf
	Return 1.0 - s
EndFunction

; A pistol in each hand: the reloading gun's clip takes the whole body, the other gun goes in the belt and cannot fire
Function DualReload(Int slot, Int other)
	shotsDual += 1
	Int mine = shotsDual
	Float side = -1.0
	If slot == RIGHT_HAND
		side = 1.0
	EndIf
	PlayerRef.SetAnimationVariableFloat(DUAL_VARIABLE, side)
	PlayerRef.SendModEvent("ZP_FlintlockHolster", other as String, DUAL_LOCK * Pace())
	HoldReload(slot, DUAL_RESET_AFTER * Pace())
	If mine == shotsDual
		PlayerRef.SetAnimationVariableFloat(DUAL_VARIABLE, 0.0)
	EndIf
EndFunction
