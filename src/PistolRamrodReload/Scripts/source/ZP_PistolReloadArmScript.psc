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
arm's idle there is whatever moveset wins, so both fade over FADE_STEPS instead of switching. A shield in the left
hand (2026-11-03) is the same for a right-hand pistol: the clip slings it on the back, and STOW_VARIABLE frees the shield
pose (0_master's MRh_Shd_Blend).
A torch in the left hand (2026-11-05) is the same as a shield: the clip lowers it into a loop on the belt, still lit,
reloads and takes it back up, and STOW_VARIABLE frees the torch pose (0_master's MRh_Torch_Blend). (The first answer
the same day unequipped it into the inventory for the empty hand's reload and equipped it again: curator, "add
animation that lowers the torch to put it away rather than just spawning and despawning the torch".)
A spell in the other hand (2026-11-07; a player: "No reload animation when holding a pistol and spell in the other
hand"): the magic graph's staff-and-spell blend keeps the spell hand's arm on its own graph while the gun casts. The
patch wraps it on DUAL_VARIABLE too, which SpellReload fades to the gun's side for the reload (its clip then owns the
body: the one-gun reload, resting on the spell idle) and back SPELL_RESET_AFTER later.
Pistols are recognised by Loop's keyword (KID gives it to the Gentleman's pistols; Reversal Shadow carries it), looked
up by FormID, so this plugin does not master Loop's. (Prophecy's Hair Trigger played faster twins of the clips for a
few hours on 2026-11-02; the curator took its faster reload out of the talent, so every reload is one pace.)}

Actor Property PlayerRef Auto
String Property ARM_VARIABLE = "fZenPistolRightArmIdle" AutoReadOnly    ; pistol left: the free right arm (1hm_behavior)
String Property LEFT_ARM_VARIABLE = "fZenPistolLeftArmIdle" AutoReadOnly ; pistol right: the free left arm (0_master)
String Property DUAL_VARIABLE = "fZenPistolDualReload" AutoReadOnly     ; two pistols: -1 left gun's clip, +1 right's
String Property STOW_VARIABLE = "fZenPistolLeftStow" AutoReadOnly       ; pistol right, melee weapon left (0_master)
String Property SHIELD_VARIABLE = "fZenPistolShieldIdle" AutoReadOnly   ; pistol right, shield left, third person
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
; a melee weapon's arm goes back to the game's idle on the clip's ARM_BACK_EVENT, just after the regrip (tools/01
; ARM_BACK): on a timer the hand-back landed after the clip had ended (Hair Trigger's) or on its held end, and the arm
; showed the staff idle's or vanilla's weapon-holding pose before the game's own (SIGMA's, by stance) came (curator
; 2026-11-02). STOW_RESET_AFTER is the fallback: no event (Pandora not rerun) or the reload cut short.
String Property ARM_BACK_EVENT = "ZenPistolArmBack" AutoReadOnly
Float Property STOW_RESET_AFTER = 2.7 AutoReadOnly
String Property LoopPlugin = "Pistol animation by Loop.esp" AutoReadOnly
Int Property LOOP_KEYWORD_ID = 0x801 AutoReadOnly   ; Pistol_Animation_By_Loop
Int Property LEFT_HAND = 0 AutoReadOnly              ; the Flintlock script's hand / GetEquippedItemType hand
Int Property RIGHT_HAND = 1 AutoReadOnly
Int Property TYPE_STAFF = 8 AutoReadOnly             ; GetEquippedItemType
Int Property TYPE_SHIELD = 10 AutoReadOnly
Int Property TYPE_TORCH = 11 AutoReadOnly
Int Property TYPE_SPELL = 9 AutoReadOnly
; a spell reload's clip (tools/01 SPELL_HOLD): the motion ends at 2.11 s after the hand-over, then it holds the spell
; idle 0.5 s more; the body goes back inside that hold (after the clip the gun's graph shows Loop's free arm)
Float Property SPELL_RESET_AFTER = 2.2 AutoReadOnly

Keyword pistolKeyword
Int shotsSpell  ; spell reloads started: the newest owns the reset
Int shots       ; the newest shot owns the reset, per hand
Int shotsRight
Int shotsDual
Int stows       ; melee stows started; stowOpen: the one ARM_BACK_EVENT hands back (0: none)
Int stowOpen
String stowVariable
Bool stowShare
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
	If Game.GetModByName(LoopPlugin) != 255
		pistolKeyword = Game.GetFormFromFile(LOOP_KEYWORD_ID, LoopPlugin) as Keyword
	EndIf
	PlayerRef.SetAnimationVariableFloat(ARM_VARIABLE, 1.0)
	PlayerRef.SetAnimationVariableFloat(LEFT_ARM_VARIABLE, 1.0)
	PlayerRef.SetAnimationVariableFloat(DUAL_VARIABLE, 0.0)
	PlayerRef.SetAnimationVariableFloat(STOW_VARIABLE, 1.0)
	PlayerRef.SetAnimationVariableFloat(REQUEST_L, 0.0)
	PlayerRef.SetAnimationVariableFloat(REQUEST_R, 0.0)
	SyncShield()
EndFunction

Event OnObjectEquipped(Form akBaseObject, ObjectReference akReference)
	SyncShield()
EndEvent

Event OnObjectUnequipped(Form akBaseObject, ObjectReference akReference)
	SyncShield()
EndEvent

; Third person, a pistol in the right hand and a shield in the left (2026-11-03): SHIELD_VARIABLE at 0 hands the shield
; hand to the magic graph, whose Loop clips carry the one-handed shield arm (the Pandora patch's MRh_Shield_Ready blend;
; tools/07); 1 otherwise, vanilla. Blocking leaves that state, so the block plays its own shield block.
Function SyncShield()
	Float value = 1.0
	Weapon gun = PlayerRef.GetEquippedWeapon(False)
	If pistolKeyword && gun && gun.HasKeyword(pistolKeyword) && PlayerRef.GetEquippedItemType(LEFT_HAND) == TYPE_SHIELD
		value = 0.0
	EndIf
	PlayerRef.SetAnimationVariableFloat(SHIELD_VARIABLE, value)
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
	ElseIf otherType == TYPE_SHIELD || otherType == TYPE_TORCH  ; on the arm or back / in the belt (left-hand only items)
		If slot == RIGHT_HAND
			StowReload(slot)
		EndIf
		Return
	ElseIf otherType == TYPE_SPELL              ; the spell hand loads and rams
		SpellReload(slot)
		Return
	ElseIf otherType != 0
		Return
	EndIf
	If slot == LEFT_HAND
		shots += 1
		Int mine = shots
		PlayerRef.SetAnimationVariableFloat(ARM_VARIABLE, 0.0)
		HoldReload(slot, RESET_AFTER)
		If mine == shots
			PlayerRef.SetAnimationVariableFloat(ARM_VARIABLE, 1.0)
		EndIf
	Else
		shotsRight += 1
		Int mineRight = shotsRight
		PlayerRef.SetAnimationVariableFloat(LEFT_ARM_VARIABLE, 0.0)
		HoldReload(slot, RESET_AFTER)
		If mineRight == shotsRight
			PlayerRef.SetAnimationVariableFloat(LEFT_ARM_VARIABLE, 1.0)
		EndIf
	EndIf
EndFunction

; A melee weapon in the other hand: that arm fades to the clip, which sheathes the weapon, reloads and draws it again
; (the two-pistol timeline), and back to the game's idle on the clip's ARM_BACK_EVENT, right after the regrip, while
; the draw still moves it (OnAnimationEvent); STOW_RESET_AFTER after the hand-over if no event came
Function StowReload(Int slot)
	String var = ARM_VARIABLE
	Bool share = True
	If slot != LEFT_HAND
		var = STOW_VARIABLE
		share = False
	EndIf
	stows += 1
	Int mine = stows
	stowVariable = var
	stowShare = share
	stowOpen = mine
	RegisterForAnimationEvent(PlayerRef, ARM_BACK_EVENT)    ; every time: the graph may be new since the last
	FadeOut(var, share)
	HoldReload(slot, STOW_RESET_AFTER)
	If stowOpen == mine
		stowOpen = 0
		FadeIn(var, share)
	EndIf
EndFunction

; The stow clip's ARM_BACK_EVENT (both views' clips carry it: the first one hands the arm back)
Event OnAnimationEvent(ObjectReference akSource, String asEventName)
	If asEventName == ARM_BACK_EVENT && stowOpen != 0
		stowOpen = 0
		FadeIn(stowVariable, stowShare)
	EndIf
EndEvent

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

; A spell in the other hand: DUAL_VARIABLE (the Pandora patch's wrapper round the staff-and-spell blend) fades to the
; gun's side over FADE_STEPS sets, so its clip takes the whole body, and back SPELL_RESET_AFTER after the hand-over,
; inside the clip's held end on the spell idle. A fade, not a switch, so a spell idle the clip did not rest on (a
; moving or sneaking one) blends in instead of snapping
Function SpellReload(Int slot)
	shotsSpell += 1
	Int mine = shotsSpell
	Float side = -1.0
	If slot == RIGHT_HAND
		side = 1.0
	EndIf
	Int i = 1
	While i <= FADE_STEPS
		PlayerRef.SetAnimationVariableFloat(DUAL_VARIABLE, side * i / FADE_STEPS)
		i += 1
	EndWhile
	HoldReload(slot, SPELL_RESET_AFTER)
	If mine == shotsSpell
		i = FADE_STEPS - 1
		While i >= 0
			PlayerRef.SetAnimationVariableFloat(DUAL_VARIABLE, side * i / FADE_STEPS)
			i -= 1
		EndWhile
	EndIf
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
	PlayerRef.SendModEvent("ZP_FlintlockHolster", other as String, DUAL_LOCK)
	HoldReload(slot, DUAL_RESET_AFTER)
	If mine == shotsDual
		PlayerRef.SetAnimationVariableFloat(DUAL_VARIABLE, 0.0)
	EndIf
EndFunction
