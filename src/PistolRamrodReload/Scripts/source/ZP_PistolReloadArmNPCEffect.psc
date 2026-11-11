Scriptname ZP_PistolReloadArmNPCEffect extends ActiveMagicEffect
{Zenderal - Pistol Ramrod Reload: enemies reload their pistols as the player does (2026-11-11, a player's report via the
curator: "enemies need the same reloads or it is unbalanced").
Since reload on demand (2026-11-02) a pistol shot plays Loop's shot alone and the reload is a separate cast the player
asks for (ZP_PistolReloadArmScript.OnDryReload); nothing asked for an NPC's. Traced 2026-11-11 (two Marauders): an NPC's
staff spends charge (2 -> 1 at the shot, cost 1); at 1 the AI treats the pistol as empty and puts it away within
0.8-2.4 s, takes it out again every ~5 s and puts it away again: one shot per enemy. Shot clips carrying the reload
(tried the same day) cannot hold an AI back: refilled during the clip, any interruption (the re-cast window 0.337-0.667 s,
a melee swing, a weapon swap) let it fire again at once.
So, the player's mechanism on the NPC: a shot leaves the gun empty (EMPTY, 1: the AI keeps taking it out but does not
fire it); while the NPC holds an empty pistol drawn and is not casting, attacking or staggered, this starts the reload
cast exactly as OnDryReload does (the hand's request variable, bWantCast<side>, M?h_SpellAimedStart,
M?h_SpellRelease_Event; the cast runs at DRY, under the shot's cost, so no bullet). OAR plays the player's reload clip
through tools/08's "<submod>, NPC" twins, gated on "not the player" and that hand's item charge under 1.5: the player's
own submods want the request variable at 1, and traced 2026-11-11 that never held for an NPC (the script sets it
anyway). This hands the free side over (HandleReload, the player's times); the clip's ZenPistolLoaded<L/R> beat fills the gun (MaxCharge:
the AI fires only a full one). A reload cut short leaves it empty, and the next time the NPC holds it the reload starts
again (fourth test: at charge 0 the AI never took the pistol out again). A right-hand pistol with a shield shows tools/07's shield arm, as the player's does.
The ability that runs this (tools/02) is given to every NPC by SPID; its effect runs only while a staff is equipped.}

String Property ARM_VARIABLE = "fZenPistolRightArmIdle" AutoReadOnly    ; pistol left: the free right arm (1hm_behavior)
String Property LEFT_ARM_VARIABLE = "fZenPistolLeftArmIdle" AutoReadOnly ; pistol right: the free left arm (0_master)
String Property DUAL_VARIABLE = "fZenPistolDualReload" AutoReadOnly     ; two pistols / a spell: -1 left gun's, +1 right's
String Property STOW_VARIABLE = "fZenPistolLeftStow" AutoReadOnly       ; pistol right, melee weapon, shield or torch left
String Property SHIELD_VARIABLE = "fZenPistolShieldIdle" AutoReadOnly   ; pistol right, shield left, third person
String Property REQUEST_L = "fZenPistolReloadL" AutoReadOnly            ; reload asked for: 1 while its clip starts (OAR)
String Property REQUEST_R = "fZenPistolReloadR" AutoReadOnly
String Property ARM_BACK_EVENT = "ZenPistolArmBack" AutoReadOnly        ; a stow clip's hand-back (tools/01 ARM_BACK)
String Property LOADED_L = "ZenPistolLoadedL" AutoReadOnly              ; the reload clip's ball rammed home
String Property LOADED_R = "ZenPistolLoadedR" AutoReadOnly
String Property FIRE_LEFT = "MLh_SpellFire_Event" AutoReadOnly
String Property FIRE_RIGHT = "MRh_SpellFire_Event" AutoReadOnly
Int Property FADE_STEPS = 6 AutoReadOnly
; bWantCast and the request are held until the NPC's graph has taken them: it takes the bWantCast edge on its own
; update, 0.1-0.2 s later (ZenPistolNPCTrace 2026-11-11), and ZenMusketHandling 1.4.0 reads the request at BeginCast
Float Property RESET_WANT_AFTER = 0.8 AutoReadOnly
Float Property REQUEST_HOLD = 1.0 AutoReadOnly
; ZP_PistolReloadArmScript's times, counted from the hand-over at the reload clip's start
Float Property RESET_AFTER = 1.8 AutoReadOnly
Float Property DUAL_RESET_AFTER = 2.95 AutoReadOnly
Float Property STOW_RESET_AFTER = 2.7 AutoReadOnly
Float Property SPELL_RESET_AFTER = 2.2 AutoReadOnly
Float Property POLL = 0.25 AutoReadOnly                ; how often an empty pistol is looked at
; Charge (the shot costs 1; the Flintlock pistols hold 2). The AI fires a pistol only at full charge; at 1 it puts it
; away but takes it out again every ~5 s and holds it ~5 s (traced, first test); at 0 it never took it out again
; (fourth test). So an empty pistol rests at EMPTY, and the reload's own cast runs at DRY, under the shot's cost, so it
; fires nothing, back to EMPTY at its spell-fire.
Float Property EMPTY = 1.0 AutoReadOnly
Float Property DRY = 0.5 AutoReadOnly
Float Property LOADED_AFTER = 0.36 AutoReadOnly       ; after the reload cast's spell-fire: past 0.667 s however late
; The cast starts on bWantCast<side>'s false -> true edge (BeginCast_OnFalseToTrueMod), which goes false a frame first
; (EDGE_WAIT). The refusals (sixth/seventh tests) were not the edge: ZenPistolNPCTrace showed this script's
; M?h_SpellAimedStart reaching the graph before its BeginCast, 0.1-0.2 s behind (refused, then CastStop); the one reload
; that played had them in the same millisecond. ZenMusketHandling 1.4.0 (section 4) answers an NPC's BeginCast with the
; aimed cast and its release when the request is set (1.4.1: once per request); without it no reload starts and the
; fallback loads the gun. The cast is looked for every CAST_POLL up to CAST_WAIT; once it shows, bWantCast and the
; request go back at once and the arms are handed over.
Float Property EDGE_WAIT = 0.05 AutoReadOnly
Float Property CAST_POLL = 0.05 AutoReadOnly
Float Property CAST_WAIT = 0.8 AutoReadOnly
; Fallback: an NPC that has held its empty pistol drawn this long without a reload loading it gets it loaded with no
; animation (melee swings and weapon swaps cut most reloads short; sixth test), so it cannot fire faster than about
; one reload but is never stuck with an empty gun.
Float Property FALLBACK_LOAD = 4.0 AutoReadOnly
String Property LoopPlugin = "Pistol animation by Loop.esp" AutoReadOnly
Int Property LOOP_KEYWORD_ID = 0x801 AutoReadOnly      ; Pistol_Animation_By_Loop
Int Property LEFT_HAND = 0 AutoReadOnly
Int Property RIGHT_HAND = 1 AutoReadOnly
Int Property TYPE_STAFF = 8 AutoReadOnly               ; GetEquippedItemType
Int Property TYPE_SPELL = 9 AutoReadOnly
Int Property TYPE_SHIELD = 10 AutoReadOnly
Int Property TYPE_TORCH = 11 AutoReadOnly
; 2026-11-11 trace: effect start/finish, shots, reloads asked for, loads, and every 2 s in combat the hands' state
; (Papyrus log, [ZP PistolReload NPC]); off since the twelfth test showed the enemy reload working
Bool Property TRACE = False AutoReadOnly

Actor npc
Keyword pistolKeyword
Bool live
Bool reloading        ; a reload this script started is playing (one at a time, as the player's)
Float kickTime        ; when the last reload was asked for (0: its resets done)
Float emptyLeft       ; since when that hand's pistol has been held drawn and empty (0: not)
Float emptyRight
; Per hand: shots fired (genL/R, counted first thing in the shot's handler, before any native call can yield), the
; count when the playing reload started (reloadGenL/R), and whether the next spell-fire is the reload's own cast
; (dryL/R). Papyrus delivered a reload's ZenPistolLoaded after the next shot (tenth test: shot 31 s, "loaded" 32 s,
; a second shot 33 s with no reload): a load only counts while no shot has come since its reload began.
Int genL
Int genR
Int reloadGenL
Int reloadGenR
Bool dryL
Bool dryR
String kickSide
String kickRequest
Int ticks
Int shots             ; the newest reload owns the reset, per kind
Int shotsRight
Int shotsDual
Int shotsSpell
Int stows
Int stowOpen
String stowVariable
Bool stowShare

Event OnEffectStart(Actor akTarget, Actor akCaster)
	npc = akTarget
	If !npc || npc == Game.GetPlayer()
		Return
	EndIf
	If Game.GetModByName(LoopPlugin) != 255
		pistolKeyword = Game.GetFormFromFile(LOOP_KEYWORD_ID, LoopPlugin) as Keyword
	EndIf
	If !pistolKeyword
		Return
	EndIf
	live = True
	Settle(LEFT_HAND)
	Settle(RIGHT_HAND)
	Note("effect on")
	Register()
	RegisterForSingleUpdate(POLL)
EndEvent

; the target's 3D (re)loaded: a new graph keeps no animation event registrations and starts on its defaults
Event OnLoad()
	Register()
EndEvent

Function Register()
	If !live
		Return
	EndIf
	RegisterForAnimationEvent(npc, FIRE_LEFT)
	RegisterForAnimationEvent(npc, FIRE_RIGHT)
	RegisterForAnimationEvent(npc, ARM_BACK_EVENT)
	RegisterForAnimationEvent(npc, LOADED_L)
	RegisterForAnimationEvent(npc, LOADED_R)
	SyncShield()
EndFunction

; the staff put away (the effect's condition): the graph's defaults back, whatever was handed over or asked for
Event OnEffectFinish(Actor akTarget, Actor akCaster)
	If !live
		Return
	EndIf
	Note("effect off")
	live = False
	stowOpen = 0
	npc.SetAnimationVariableFloat(ARM_VARIABLE, 1.0)
	npc.SetAnimationVariableFloat(LEFT_ARM_VARIABLE, 1.0)
	npc.SetAnimationVariableFloat(DUAL_VARIABLE, 0.0)
	npc.SetAnimationVariableFloat(STOW_VARIABLE, 1.0)
	npc.SetAnimationVariableFloat(SHIELD_VARIABLE, 1.0)
	npc.SetAnimationVariableFloat(REQUEST_L, 0.0)
	npc.SetAnimationVariableFloat(REQUEST_R, 0.0)
EndEvent

Event OnObjectEquipped(Form akBaseObject, ObjectReference akReference)
	SyncShield()
EndEvent

Event OnObjectUnequipped(Form akBaseObject, ObjectReference akReference)
	SyncShield()
EndEvent

Function Note(String what)
	If TRACE && npc
		Debug.Trace("[ZP PistolReload NPC] " + npc.GetDisplayName() + " " + npc + ": " + what + " | left " + \
			npc.GetEquippedItemType(LEFT_HAND) + " charge " + npc.GetActorValue("LeftItemCharge") + ", right " + \
			npc.GetEquippedItemType(RIGHT_HAND) + " charge " + npc.GetActorValue("RightItemCharge") + \
			", casting L/R " + npc.GetAnimationVariableBool("IsCastingLeft") + "/" + \
			npc.GetAnimationVariableBool("IsCastingRight") + ", attacking " + \
			npc.GetAnimationVariableBool("IsAttacking") + ", combat " + npc.GetCombatState())
	EndIf
EndFunction

; A right-hand pistol and a shield: SHIELD_VARIABLE 0 gives the shield hand to the magic graph, whose Loop clips carry
; the one-handed shield arm (tools/07); 1 otherwise (ZP_PistolReloadArmScript.SyncShield)
Function SyncShield()
	If !live
		Return
	EndIf
	Float value = 1.0
	If IsPistol(RIGHT_HAND) && npc.GetEquippedItemType(LEFT_HAND) == TYPE_SHIELD
		value = 0.0
	EndIf
	npc.SetAnimationVariableFloat(SHIELD_VARIABLE, value)
EndFunction

Bool Function IsPistol(Int hand)
	Weapon gun = npc.GetEquippedWeapon(hand == LEFT_HAND)
	Return gun && gun.HasKeyword(pistolKeyword)
EndFunction

String Function ChargeAV(Int hand)
	If hand == LEFT_HAND
		Return "LeftItemCharge"
	EndIf
	Return "RightItemCharge"
EndFunction

Float Function MaxCharge(Int hand)
	Return WornObject.GetItemMaxCharge(npc, hand, 0)
EndFunction

; ZP_FlintlockAmmoPlayerScript.SetCharge on the NPC: Restore/Damage first; Restore only gives back damaged charge, so
; Set, then Force, for what does not take
Function SetCharge(Int hand, Float value)
	String av = ChargeAV(hand)
	Float cur = npc.GetActorValue(av)
	If value > cur
		npc.RestoreActorValue(av, value - cur)
	ElseIf value < cur
		npc.DamageActorValue(av, cur - value)
	EndIf
	If Math.Abs(npc.GetActorValue(av) - value) < 0.01
		Return
	EndIf
	npc.SetActorValue(av, value)
	If Math.Abs(npc.GetActorValue(av) - value) < 0.01
		Return
	EndIf
	npc.ForceActorValue(av, value)
EndFunction

; A pistol is loaded at its full charge or empty at EMPTY; one below EMPTY (an earlier build's 0, a reload's DRY cut
; short) is set to EMPTY, so the AI keeps taking it out
Function Settle(Int hand)
	If IsPistol(hand) && npc.GetActorValue(ChargeAV(hand)) < EMPTY - 0.01
		SetCharge(hand, EMPTY)
	EndIf
EndFunction

Event OnAnimationEvent(ObjectReference akSource, String asEventName)
	If !live
		Return
	EndIf
	If asEventName == ARM_BACK_EVENT
		If stowOpen != 0
			stowOpen = 0
			FadeIn(stowVariable, stowShare)
		EndIf
		Return
	EndIf
	If asEventName == LOADED_L || asEventName == LOADED_R
		Int hand = LEFT_HAND
		If asEventName == LOADED_R
			hand = RIGHT_HAND
		EndIf
		Load(hand, ReloadGen(hand), "loaded")
		Return
	EndIf
	Int slot = LEFT_HAND
	If asEventName == FIRE_RIGHT
		slot = RIGHT_HAND
	EndIf
	; pure script state first: a real shot counts before anything can yield
	Bool ownCast = dryL
	If slot == RIGHT_HAND
		ownCast = dryR
	EndIf
	If !ownCast
		CountShot(slot)
	EndIf
	If !IsPistol(slot)
		Return
	EndIf
	If ownCast && npc.GetActorValue(ChargeAV(slot)) < EMPTY - 0.25    ; the reload's own cast (DRY: no bullet)
		SetDry(slot, False)
		SetCharge(slot, EMPTY)
		Note("hand " + slot + " reload cast, empty again")
		; ninth test: at EMPTY the AI put the pistol away ~1.5 s into most reloads (nothing else cut them: no swing, no
		; stagger), as it does any pistol it cannot fire. Past the reload clip's re-cast window (0.337-0.667 s; this event
		; is at 0.334) the pistol counts as loaded while its reload plays: the release state holds the next shot until
		; the clip ends, and a reload cut short after that point leaves a loaded gun
		Utility.Wait(LOADED_AFTER)
		If live && npc.GetAnimationVariableBool(Casting(slot))
			Load(slot, ReloadGen(slot), "counts as loaded while its reload plays")
		EndIf
	Else                                                       ; a real shot: full - 1
		If ownCast                                             ; at a charge only a real shot has: count it after all
			SetDry(slot, False)
			CountShot(slot)
		EndIf
		SetCharge(slot, EMPTY)
		Note("hand " + slot + " shot, now empty")
	EndIf
EndEvent

Int Function Gen(Int hand)
	If hand == LEFT_HAND
		Return genL
	EndIf
	Return genR
EndFunction

Int Function ReloadGen(Int hand)
	If hand == LEFT_HAND
		Return reloadGenL
	EndIf
	Return reloadGenR
EndFunction

Function CountShot(Int hand)
	If hand == LEFT_HAND
		genL += 1
	Else
		genR += 1
	EndIf
EndFunction

Function SetDry(Int hand, Bool value)
	If hand == LEFT_HAND
		dryL = value
	Else
		dryR = value
	EndIf
EndFunction

; Full charge for that hand's reload, which began at shot count `since`: not if a shot has come since (a late event),
; and back to EMPTY if one came while the charge was being written
Function Load(Int hand, Int since, String why)
	If !live || Gen(hand) != since || !IsPistol(hand)
		Return
	EndIf
	SetCharge(hand, MaxCharge(hand))
	If Gen(hand) != since
		SetCharge(hand, EMPTY)
		Return
	EndIf
	Note("hand " + hand + " " + why)
EndFunction

; Every POLL: the reload's resets (bWantCast, the request), then an empty pistol's reload; a trace line every 2 s in
; combat. The next update is asked for first: HandleReload holds this one for seconds.
Event OnUpdate()
	If !live
		Return
	EndIf
	RegisterForSingleUpdate(POLL)
	If kickTime > 0.0
		Float since = Utility.GetCurrentRealTime() - kickTime
		If since >= RESET_WANT_AFTER
			npc.SetAnimationVariableBool("bWantCast" + kickSide, False)
		EndIf
		If since >= REQUEST_HOLD
			npc.SetAnimationVariableFloat(kickRequest, 0.0)
			kickTime = 0.0
		EndIf
	EndIf
	ticks += 1
	If TRACE && ticks % 8 == 0 && npc.GetCombatState() != 0
		Note("tick")
	EndIf
	If !npc.IsWeaponDrawn() || npc.IsDead()
		emptyLeft = 0.0
		emptyRight = 0.0
		Return
	EndIf
	Fallback(LEFT_HAND)
	Fallback(RIGHT_HAND)
	If reloading || kickTime > 0.0 || npc.IsBleedingOut()
		Return
	EndIf
	If npc.GetAnimationVariableBool("IsCastingLeft") || npc.GetAnimationVariableBool("IsCastingRight") || \
			npc.GetAnimationVariableBool("IsAttacking") || npc.GetAnimationVariableBool("IsStaggering")
		Return
	EndIf
	Int hand = LEFT_HAND
	While hand <= RIGHT_HAND
		If !reloading && IsPistol(hand) && npc.GetActorValue(ChargeAV(hand)) < MaxCharge(hand) - 0.01
			DryReload(hand)
		EndIf
		hand += 1
	EndWhile
EndEvent

; FALLBACK_LOAD: how long this hand's pistol has been held drawn and empty; past it (and no reload playing), loaded
Function Fallback(Int hand)
	Float since = emptyLeft
	If hand == RIGHT_HAND
		since = emptyRight
	EndIf
	If !IsPistol(hand) || npc.GetActorValue(ChargeAV(hand)) >= MaxCharge(hand) - 0.01
		since = 0.0
	ElseIf since <= 0.0
		since = Utility.GetCurrentRealTime()
	ElseIf !reloading && Utility.GetCurrentRealTime() - since >= FALLBACK_LOAD
		SetCharge(hand, MaxCharge(hand))
		Note("hand " + hand + " loaded without the clip (held empty " + FALLBACK_LOAD + " s)")
		since = 0.0
	EndIf
	If hand == LEFT_HAND
		emptyLeft = since
	Else
		emptyRight = since
	EndIf
EndFunction

; ZP_PistolReloadArmScript.OnDryReload on the NPC: the reload's cast started the engine's way, with that hand's request
; variable at 1 (and tools/08's twins: item charge under 1.5) for the reload clip's OAR conditions; the arms handed over
; as the clip starts
Function DryReload(Int slot)
	String side = "Left"
	String request = REQUEST_L
	If slot == RIGHT_HAND
		side = "Right"
		request = REQUEST_R
	EndIf
	reloading = True
	If slot == LEFT_HAND
		reloadGenL = genL
	Else
		reloadGenR = genR
	EndIf
	SetDry(slot, True)                   ; the next spell-fire of this hand is this cast's (no bullet)
	Bool wanted = npc.GetAnimationVariableBool("bWantCast" + side)
	SetCharge(slot, DRY)
	npc.SetAnimationVariableFloat(request, 1.0)
	npc.SetAnimationVariableBool("bWantCast" + side, False)
	Utility.Wait(EDGE_WAIT)
	npc.SetAnimationVariableBool("bWantCast" + side, True)
	; No M?h_SpellAimedStart / Release of our own any more: ZenMusketHandling answers the graph's BeginCast with them.
	; Sent from here they came in just after its answer and restarted the aimed cast, which threw the reload away; the
	; graph then raised a second BeginCast (bWantCast still held) and that answer fired a real shot (11th test, 22:06:26)
	kickSide = side
	kickRequest = request
	kickTime = Utility.GetCurrentRealTime()
	Float until = kickTime + CAST_WAIT     ; the gun stays at DRY all along: a late start must find it there at its spell-fire
	Bool started = False
	While live && !started && Utility.GetCurrentRealTime() < until
		Utility.Wait(CAST_POLL)
		started = live && npc.GetAnimationVariableBool(Casting(slot))
	EndWhile
	If started                             ; let go of the cast request at once: no second BeginCast from it
		npc.SetAnimationVariableBool("bWantCast" + side, False)
		npc.SetAnimationVariableFloat(request, 0.0)
	EndIf
	If started
		Note("hand " + slot + " reload started (bWantCast was " + wanted + ")")
		HandleReload(slot, 1 - slot)
	ElseIf live
		If npc.GetActorValue(ChargeAV(slot)) < EMPTY - 0.01
			SetCharge(slot, EMPTY)
		EndIf
		Note("hand " + slot + " reload refused (bWantCast was " + wanted + ")")
	EndIf
	SetDry(slot, False)
	reloading = False
EndFunction

String Function Casting(Int slot)
	If slot == LEFT_HAND
		Return "IsCastingLeft"
	EndIf
	Return "IsCastingRight"
EndFunction

; `seconds` while that hand's reload plays: a reload cut short gives the arms back at once
Function HoldReload(Int slot, Float seconds)
	Float until = Utility.GetCurrentRealTime() + seconds
	String casting = Casting(slot)
	While live && Utility.GetCurrentRealTime() < until && npc.GetAnimationVariableBool(casting)
		Utility.Wait(0.1)
	EndWhile
EndFunction

; The arms for the reload clip, by what the other hand holds (its OAR submods' conditions)
Function HandleReload(Int slot, Int other)
	Int otherType = npc.GetEquippedItemType(other)
	If otherType == TYPE_STAFF
		If IsPistol(other)
			DualReload(slot)
		EndIf
		Return
	ElseIf otherType >= 1 && otherType <= 4     ; sword, dagger, axe, mace: sheathed for the reload
		StowReload(slot)
		Return
	ElseIf otherType == TYPE_SHIELD || otherType == TYPE_TORCH  ; left-hand only items
		If slot == RIGHT_HAND
			StowReload(slot)
		EndIf
		Return
	ElseIf otherType == TYPE_SPELL
		SpellReload(slot)
		Return
	ElseIf otherType != 0
		Return
	EndIf
	If slot == LEFT_HAND
		shots += 1
		Int mine = shots
		npc.SetAnimationVariableFloat(ARM_VARIABLE, 0.0)
		HoldReload(slot, RESET_AFTER)
		If live && mine == shots
			npc.SetAnimationVariableFloat(ARM_VARIABLE, 1.0)
		EndIf
	Else
		shotsRight += 1
		Int mineRight = shotsRight
		npc.SetAnimationVariableFloat(LEFT_ARM_VARIABLE, 0.0)
		HoldReload(slot, RESET_AFTER)
		If live && mineRight == shotsRight
			npc.SetAnimationVariableFloat(LEFT_ARM_VARIABLE, 1.0)
		EndIf
	EndIf
EndFunction

; A melee weapon (or a right-hand pistol's shield or torch) in the other hand: that arm fades to the clip, which puts
; the item away, reloads and takes it again, and back on the clip's ARM_BACK_EVENT (OnAnimationEvent)
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
	FadeOut(var, share)
	HoldReload(slot, STOW_RESET_AFTER)
	If live && stowOpen == mine
		stowOpen = 0
		FadeIn(var, share)
	EndIf
EndFunction

Function FadeOut(String var, Bool share)
	Int i = 1
	While i < FADE_STEPS
		npc.SetAnimationVariableFloat(var, ArmWeight(i as Float / FADE_STEPS, share))
		i += 1
	EndWhile
	npc.SetAnimationVariableFloat(var, 0.0)
EndFunction

Function FadeIn(String var, Bool share)
	Int i = FADE_STEPS - 1
	While i > 0
		npc.SetAnimationVariableFloat(var, ArmWeight(i as Float / FADE_STEPS, share))
		i -= 1
	EndWhile
	npc.SetAnimationVariableFloat(var, 1.0)
EndFunction

; the free arm's variable for the clip's share s of the arm (0 < s < 1; ZP_PistolReloadArmScript.ArmWeight)
Float Function ArmWeight(Float s, Bool share)
	If share
		Return 0.01 * (1.0 - s) / s
	EndIf
	Return 1.0 - s
EndFunction

; A spell in the other hand: DUAL_VARIABLE fades to the gun's side, so its clip takes the whole body, and back
Function SpellReload(Int slot)
	shotsSpell += 1
	Int mine = shotsSpell
	Float side = -1.0
	If slot == RIGHT_HAND
		side = 1.0
	EndIf
	Int i = 1
	While i <= FADE_STEPS
		npc.SetAnimationVariableFloat(DUAL_VARIABLE, side * i / FADE_STEPS)
		i += 1
	EndWhile
	HoldReload(slot, SPELL_RESET_AFTER)
	If live && mine == shotsSpell
		i = FADE_STEPS - 1
		While i >= 0
			npc.SetAnimationVariableFloat(DUAL_VARIABLE, side * i / FADE_STEPS)
			i -= 1
		EndWhile
	EndIf
EndFunction

; A pistol in each hand: the reloading gun's clip takes the whole body (the other gun goes in the belt and comes back)
Function DualReload(Int slot)
	shotsDual += 1
	Int mine = shotsDual
	Float side = -1.0
	If slot == RIGHT_HAND
		side = 1.0
	EndIf
	npc.SetAnimationVariableFloat(DUAL_VARIABLE, side)
	HoldReload(slot, DUAL_RESET_AFTER)
	If live && mine == shotsDual
		npc.SetAnimationVariableFloat(DUAL_VARIABLE, 0.0)
	EndIf
EndFunction
