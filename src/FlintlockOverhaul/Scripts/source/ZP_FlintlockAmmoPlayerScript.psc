Scriptname ZP_FlintlockAmmoPlayerScript extends ReferenceAlias
{Zenderal - Flintlock Overhaul. A Gentleman's Flintlock Armoury's pistols are staves, so their
"ammo" is enchantment charge. This script owns that charge on the PLAYER's pistols:
  - a pistol in hand is either LOADED (charge = max) or EMPTY (charge = 0), tracked here;
  - firing empties it, and 2 s later one Flintlock Bullet is taken to load it again;
  - equipping a pistol ignores its stored charge and loads it from a bullet;
  - unequipping a loaded pistol gives the bullet back;
  - charge added by a soul gem in the inventory menu is removed again.
Also adds the hidden perk that scales shot damage like a bow.
Prophecy's pistol talents (2026-11-01), looked up by FormID so this plugin does not master Prophecy: Hair Trigger's
reloads are animated like any other (2026-11-02, curator: skipped, they let the guns spam), Pistol Ramrod Reload playing
faster clips for it (its tools/07), and only where no clip plays it loads by timer in HairTriggerDelay; while Fan the
Hammer's effect is on a pistol reloads in FanDelay, by timer, with no animation (the power's text); mod event
ZP_FlintlockReload (ZenProphecyRage.dll, Blade and Barrel's melee hits) loads every pending hand at once, at most
once every BladeReloadCooldown seconds (counted from a reload it actually made; curator 2026-11-01).
Mod event ZP_FlintlockHolster (Zenderal - Pistol Ramrod Reload, 2026-11-02: a reload with a pistol in each hand tucks
the other gun in the belt): that hand (strArg "0" left, "1" right) holds no charge for numArg seconds, so it cannot
fire, and gets it back after if it is the same gun and still loaded. A save loaded mid-holster is repaired in Setup.
Overlapping holsters keep the charge off until the latest one ends, and a gun loaded while holstered stays at 0 charge
until then.
Loaded by its reload animation (2026-11-02, curator: an attack cut the reload short and the timer loaded the gun
anyway): where Pistol Ramrod Reload plays a reload (AnimatedReload: Loop's pistols, the other hand empty, a pistol or a
one-handed melee weapon, not mounted, not under Fan the Hammer), the gun loads on the clip's ZenPistolLoadedL / R
event, the ball rammed home; a reload cut short leaves it empty, with no timer. The shot plays no reload (2026-11-02,
curator: the other hand stays free until the player asks): pressing that hand's attack on the empty gun clicks and asks
Pistol Ramrod Reload for the reload (mod event ZP_PistolDryReload): a cast with no shot, whose spell-fire action
reaches OnActorAction like a shot (no projectile: the gun has no charge) and whose clip loads the gun. No timer behind
it (2026-11-02: a 1.6 s fallback loaded a gun whose requested reload an attack cut short); a request the graph refuses
(mid-attack) leaves the gun empty for the next press. Not while its reload still plays (IsCastingLeft / Right), while
the other pistol fires or reloads (one reload at a time), within DRY_LOCK of the last request, or holstered. Elsewhere
ReloadDelay's timer, as before. Per hand.
NPCs are untouched.}

Actor Property PlayerRef Auto
FormList Property ZP_FlintlockWeapons Auto
MiscObject Property ZP_FlintlockBullet Auto
Perk Property ZP_FlintlockArcheryScaling Auto  ; shot damage scales with Archery + bow talents
Float Property ReloadDelay = 2.0 Auto
Float Property HairTriggerDelay = 1.2 AutoReadOnly
Float Property FanDelay = 0.1 AutoReadOnly
Float Property BladeReloadCooldown = 15.0 AutoReadOnly   ; Prophecy's PISTOL['BladeReloadCooldown'] (its text)
String Property ProphecyPlugin = "Zenderal - Prophecy.esp" AutoReadOnly
Int Property HAIR_TRIGGER_ID = 0xB12 AutoReadOnly   ; ZP_Prophecy_HairTrigger
Int Property FAN_EFFECT_ID = 0xB21 AutoReadOnly     ; ZP_Prophecy_FanTheHammer_Effect
Bool Property DebugMode = False AutoReadOnly  ; ReadOnly: not stored in saves, so flipping it takes effect everywhere
String Property ReloadPlugin = "Zenderal - Pistol Ramrod Reload.esp" AutoReadOnly
String Property LoopPlugin = "Pistol animation by Loop.esp" AutoReadOnly
Int Property LOOP_KEYWORD_ID = 0x801 AutoReadOnly      ; Pistol_Animation_By_Loop: the pistols the reload clips cover
String Property LOADED_EVENT_L = "ZenPistolLoadedL" AutoReadOnly
String Property LOADED_EVENT_R = "ZenPistolLoadedR" AutoReadOnly
String Property OLD_PROP_EVENT = "AnimObjLoad" AutoReadOnly  ; registered by the first build (saves keep it)
Float Property DRY_LOCK = 0.5 AutoReadOnly         ; one request per press: its cast is on (IsCasting) ~0.1 s after
Int Property DRY_CLICK_ID = 0x0C1912 AutoReadOnly  ; UILockpickingCylinderStop (Skyrim.esm): the empty gun's click
Int Property TYPE_STAFF = 8 AutoReadOnly           ; GetEquippedItemType

; Hand 0 = left, 1 = right (SKSE's WornObject / OnActorAction slot numbering)
Weapon wepL
Weapon wepR
Bool loadedL
Bool loadedR
Bool pendingL
Bool pendingR
Perk hairTrigger      ; None without Prophecy; looked up again on every load
MagicEffect fanEffect
Float lastBladeReload = -1000.0   ; real time of Blade and Barrel's last reload
Int holsterL        ; holsters started, per hand
Int holsterR
Float holsterUntilL ; real time the latest holster on that hand ends (0: none; reset on load, real time restarts)
Float holsterUntilR
Float loadAtL       ; real time a fired gun loads by timer (0: no timer)
Float loadAtR
Bool animL          ; that hand's pending gun reloads by animation (AnimatedReload at its shot)
Bool animR
Float dryAtL        ; real time of that hand's last reload request (OnControlDown)
Float dryAtR
Sound dryClick
Keyword loopKeyword ; None without Loop's plugin (then every pistol reloads by timer)

Int Property ACTION_SPELL_FIRE = 2 AutoReadOnly

; ---------------------------------------------------------------- lifecycle

Event OnInit()
	Setup()
EndEvent

Event OnPlayerLoadGame()
	Setup()
EndEvent

Function Setup()
	If !PlayerRef.HasPerk(ZP_FlintlockArcheryScaling)
		PlayerRef.AddPerk(ZP_FlintlockArcheryScaling)
	EndIf
	RegisterForActorAction(ACTION_SPELL_FIRE)
	RegisterForMenu("InventoryMenu")
	AddInventoryEventFilter(ZP_FlintlockBullet)
	RegisterForModEvent("ZP_FlintlockReload", "OnReloadNow")
	RegisterForModEvent("ZP_FlintlockHolster", "OnHolster")
	RegisterForControl("Left Attack/Block")
	RegisterForControl("Right Attack/Block")
	UnregisterForAnimationEvent(PlayerRef, OLD_PROP_EVENT)
	dryClick = Game.GetFormFromFile(DRY_CLICK_ID, "Skyrim.esm") as Sound
	dryAtL = -1000.0
	dryAtR = -1000.0
	hairTrigger = None
	fanEffect = None
	lastBladeReload = -1000.0     ; real time starts again with every game launch
	holsterUntilL = 0.0           ; ... so a saved holster's end means nothing now (repaired below)
	holsterUntilR = 0.0
	loopKeyword = None
	If Game.GetModByName(LoopPlugin) != 255 && Game.GetModByName(ReloadPlugin) != 255
		loopKeyword = Game.GetFormFromFile(LOOP_KEYWORD_ID, LoopPlugin) as Keyword
	EndIf
	; a gun fired before the save: its timer is gone with the old session's real time (one reloading by animation
	; waits for the attack button, as when its reload is cut short)
	Int pend = 0
	While pend < 2
		If IsPending(pend) && !IsAnimated(pend)
			SetLoadAt(pend, Utility.GetCurrentRealTime() + CurrentDelay())
		Else
			SetLoadAt(pend, 0.0)
		EndIf
		pend += 1
	EndWhile
	ScheduleLoad()
	If Game.GetModByName(ProphecyPlugin) != 255
		hairTrigger = Game.GetFormFromFile(HAIR_TRIGGER_ID, ProphecyPlugin) as Perk
		fanEffect = Game.GetFormFromFile(FAN_EFFECT_ID, ProphecyPlugin) as MagicEffect
	EndIf
	Sync()
	; a gun still holstered when the game was saved: loaded, but its charge was taken for the holster
	Int hand = 0
	While hand < 2
		If IsPistol(WeaponIn(hand)) && IsLoaded(hand) && GetCharge(hand) < MaxCharge(hand) - 0.01
			SetCharge(hand, MaxCharge(hand))
		EndIf
		hand += 1
	EndWhile
	Dbg("ready")
EndFunction

; ---------------------------------------------------------------- firing

Event OnActorAction(Int actionType, Actor akActor, Form source, Int slot)
	If akActor != PlayerRef || actionType != ACTION_SPELL_FIRE || slot > 1
		Return
	EndIf
	Weapon w = WeaponIn(slot)
	If !IsPistol(w)
		Return
	EndIf
	If IsPending(slot)
		Dbg("hand " + slot + " reload started (asked for, no shot)")
	Else
		Dbg("fired hand " + slot + " (source " + source + "), charge now " + GetCharge(slot) + "/" + MaxCharge(slot))
	EndIf
	SetCharge(slot, 0.0)
	SetLoaded(slot, False)
	SetPending(slot, True)
	If AnimatedReload(slot, w)
		SetAnimated(slot, True)
		SetLoadAt(slot, 0.0)         ; loaded by the clip's event, or by asking again (OnControlDown)
	Else
		SetAnimated(slot, False)
		SetLoadAt(slot, Utility.GetCurrentRealTime() + CurrentDelay())
	EndIf
	ScheduleLoad()
EndEvent

; That hand's attack on its empty gun (its reload cut short): a click, and the reload asked for again
Event OnControlDown(String control)
	Int hand = 1
	If control == "Left Attack/Block"
		hand = 0
	ElseIf control != "Right Attack/Block"
		Return
	EndIf
	If Utility.IsInMenuMode() || !IsPending(hand) || !IsAnimated(hand) || !IsPistol(WeaponIn(hand))
		Return
	EndIf
	String casting = "IsCastingRight"
	String otherCasting = "IsCastingLeft"
	If hand == 0
		casting = "IsCastingLeft"
		otherCasting = "IsCastingRight"
	EndIf
	Float now = Utility.GetCurrentRealTime()
	If PlayerRef.GetAnimationVariableBool(casting) || now - DryAt(hand) < DRY_LOCK || now < HolsterUntil(hand)
		Return                       ; its reload still plays, was just asked for, or the gun is in the belt
	EndIf
	If IsPistol(WeaponIn(1 - hand)) && PlayerRef.GetAnimationVariableBool(otherCasting)
		Return                       ; the other pistol fires or reloads: one reload at a time, press again after
	EndIf
	SetDryAt(hand, now)
	If dryClick
		dryClick.Play(PlayerRef)
	EndIf
	PlayerRef.SendModEvent("ZP_PistolDryReload", hand as String)
	Dbg("hand " + hand + " empty: reload asked for")
EndEvent

; Pistol Ramrod Reload plays a reload for this shot (its OAR conditions; ZP_PistolReloadArmScript's cases)
Bool Function AnimatedReload(Int slot, Weapon w)
	If !loopKeyword || !w.HasKeyword(loopKeyword) || PlayerRef.IsOnMount()
		Return False
	EndIf
	; registered at every shot (the graph may not exist yet at OnInit); without the events (Pandora not rerun) the timer
	If !RegisterForAnimationEvent(PlayerRef, LOADED_EVENT_L) || !RegisterForAnimationEvent(PlayerRef, LOADED_EVENT_R)
		Dbg("no loaded events in the player's graph: reloading by timer")
		Return False
	EndIf
	If fanEffect && PlayerRef.HasMagicEffect(fanEffect)    ; Hair Trigger's reloads are animated too (faster clips)
		Return False
	EndIf
	Int other = 1 - slot
	Int t = PlayerRef.GetEquippedItemType(other)
	If t >= 0 && t <= 4                 ; empty, or a one-handed melee weapon (sheathed for the reload)
		Return True
	ElseIf t == TYPE_STAFF
		Weapon o = WeaponIn(other)
		Return o && o.HasKeyword(loopKeyword)
	EndIf
	Return False
EndFunction

; The ball is rammed home (the reload clip's event): that hand's gun loads
Event OnAnimationEvent(ObjectReference akSource, String asEventName)
	Int hand = 0
	If asEventName == LOADED_EVENT_R
		hand = 1
	ElseIf asEventName != LOADED_EVENT_L
		Return
	EndIf
	If IsPending(hand)
		SetPending(hand, False)
		TryLoad(hand)
		Dbg("hand " + hand + " loaded by its reload")
	EndIf
	ScheduleLoad()
EndEvent

Function SetLoadAt(Int hand, Float t)
	If hand == 0
		loadAtL = t
	Else
		loadAtR = t
	EndIf
EndFunction

; the next timer load among the pending hands
Function ScheduleLoad()
	Float now = Utility.GetCurrentRealTime()
	Float soonest = -1.0
	Int hand = 0
	While hand < 2
		Float at = loadAtR
		If hand == 0
			at = loadAtL
		EndIf
		If IsPending(hand) && at > 0.0 && (soonest < 0.0 || at < soonest)
			soonest = at
		EndIf
		hand += 1
	EndWhile
	If soonest >= 0.0
		Float wait = soonest - now
		If wait < 0.05
			wait = 0.05
		EndIf
		RegisterForSingleUpdate(wait)
	EndIf
EndFunction

Float Function CurrentDelay()
	If fanEffect && PlayerRef.HasMagicEffect(fanEffect)
		Return FanDelay
	ElseIf hairTrigger && PlayerRef.HasPerk(hairTrigger)
		Return HairTriggerDelay
	EndIf
	Return ReloadDelay
EndFunction

; Blade and Barrel (ZenProphecyRage.dll): a melee hit loads the fired pistols now
Event OnReloadNow(String eventName, String strArg, Float numArg, Form sender)
	Float now = Utility.GetCurrentRealTime()
	If now - lastBladeReload < BladeReloadCooldown
		Return
	EndIf
	Bool reloaded = False
	Int hand = 0
	While hand < 2
		If IsPending(hand)
			SetPending(hand, False)
			TryLoad(hand)
			reloaded = True
			Dbg("reloaded hand " + hand + " by a melee hit")
		EndIf
		hand += 1
	EndWhile
	If reloaded
		lastBladeReload = now
	EndIf
EndEvent

; Pistol Ramrod Reload, two pistols: the other gun is in the belt for numArg seconds and must not fire
Event OnHolster(String eventName, String strArg, Float numArg, Form sender)
	Int hand = strArg as Int
	If hand < 0 || hand > 1
		Return
	EndIf
	Weapon w = WeaponIn(hand)
	If !IsPistol(w)
		Return
	EndIf
	Float until = Utility.GetCurrentRealTime() + numArg
	If hand == 0
		holsterL += 1
		If until > holsterUntilL
			holsterUntilL = until
		EndIf
	Else
		holsterR += 1
		If until > holsterUntilR
			holsterUntilR = until
		EndIf
	EndIf
	SetCharge(hand, 0.0)
	Dbg("holstered hand " + hand + " for " + numArg + " s")
	Utility.Wait(numArg)
	; the holster that ends last gives the charge back
	If Utility.GetCurrentRealTime() >= HolsterUntil(hand) - 0.05 && WeaponIn(hand) == w && IsLoaded(hand)
		SetCharge(hand, MaxCharge(hand))
		Dbg("drew hand " + hand)
	EndIf
EndEvent

Event OnUpdate()
	Float now = Utility.GetCurrentRealTime()
	Int hand = 0
	While hand < 2
		Float at = loadAtR
		If hand == 0
			at = loadAtL
		EndIf
		If IsPending(hand) && at > 0.0 && at <= now + 0.02
			SetPending(hand, False)
			TryLoad(hand)
		EndIf
		hand += 1
	EndWhile
	ScheduleLoad()
EndEvent

; ---------------------------------------------------------------- equip / ammo pickup / menu

Event OnObjectEquipped(Form akBaseObject, ObjectReference akReference)
	If akBaseObject as Weapon
		Sync()
	EndIf
EndEvent

Event OnObjectUnequipped(Form akBaseObject, ObjectReference akReference)
	If akBaseObject as Weapon
		Sync()
	EndIf
EndEvent

Event OnItemAdded(Form akBaseItem, Int aiItemCount, ObjectReference akItemReference, ObjectReference akSourceContainer)
	; picked up bullets with an empty pistol in hand: load it
	Int hand = 0
	While hand < 2
		If IsPistol(WeaponIn(hand)) && !IsLoaded(hand) && !IsPending(hand)
			TryLoad(hand)
		EndIf
		hand += 1
	EndWhile
EndEvent

Event OnMenuClose(String menuName)
	Int hand = 0
	While hand < 2
		If IsPistol(WeaponIn(hand))
			Float expected = 0.0
			If IsLoaded(hand)
				expected = MaxCharge(hand)
			EndIf
			If GetCharge(hand) > expected + 0.01
				SetCharge(hand, expected)
				Debug.Notification("Flintlocks can't be charged with soul gems.")
			EndIf
		EndIf
		hand += 1
	EndWhile
	Sync()
EndEvent

; Re-reads both hands. A hand whose weapon changed refunds the old pistol's loaded bullet and
; loads the new pistol from scratch, ignoring whatever charge was stored on it.
Function Sync()
	Int hand = 0
	While hand < 2
		Weapon now = WeaponIn(hand)
		Weapon was = wepL
		If hand == 1
			was = wepR
		EndIf
		If now != was
			If IsPistol(was) && IsLoaded(hand)
				PlayerRef.AddItem(ZP_FlintlockBullet, 1, True)
			EndIf
			SetLoaded(hand, False)
			SetPending(hand, False)
			If hand == 0
				wepL = now
			Else
				wepR = now
			EndIf
			If IsPistol(now)
				SetCharge(hand, 0.0)
				TryLoad(hand)
			EndIf
		EndIf
		hand += 1
	EndWhile
EndFunction

Function TryLoad(Int hand)
	If !IsPistol(WeaponIn(hand))
		Return
	EndIf
	If PlayerRef.GetItemCount(ZP_FlintlockBullet) < 1
		SetCharge(hand, 0.0)
		Debug.Notification("Out of Flintlock Bullets.")
		Return
	EndIf
	PlayerRef.RemoveItem(ZP_FlintlockBullet, 1, True)
	SetLoaded(hand, True)
	If Utility.GetCurrentRealTime() < HolsterUntil(hand)
		Dbg("loaded hand " + hand + " in the belt: its charge comes back when the holster ends")
		Return
	EndIf
	SetCharge(hand, MaxCharge(hand))
	Dbg("loaded hand " + hand + ", charge now " + GetCharge(hand) + "/" + MaxCharge(hand))
EndFunction

; ---------------------------------------------------------------- helpers

Bool Function IsAnimated(Int hand)
	If hand == 0
		Return animL
	EndIf
	Return animR
EndFunction

Function SetAnimated(Int hand, Bool b)
	If hand == 0
		animL = b
	Else
		animR = b
	EndIf
EndFunction

Float Function DryAt(Int hand)
	If hand == 0
		Return dryAtL
	EndIf
	Return dryAtR
EndFunction

Function SetDryAt(Int hand, Float t)
	If hand == 0
		dryAtL = t
	Else
		dryAtR = t
	EndIf
EndFunction

Float Function HolsterUntil(Int hand)
	If hand == 0
		Return holsterUntilL
	EndIf
	Return holsterUntilR
EndFunction

Weapon Function WeaponIn(Int hand)
	Return PlayerRef.GetEquippedWeapon(hand == 0)
EndFunction

Bool Function IsPistol(Weapon w)
	Return w && ZP_FlintlockWeapons.HasForm(w)
EndFunction

String Function ChargeAV(Int hand)
	If hand == 0
		Return "LeftItemCharge"
	EndIf
	Return "RightItemCharge"
EndFunction

Float Function GetCharge(Int hand)
	Return PlayerRef.GetActorValue(ChargeAV(hand))
EndFunction

Float Function MaxCharge(Int hand)
	Return WornObject.GetItemMaxCharge(PlayerRef, hand, 0)
EndFunction

; Charge is moved with Restore/Damage first, the calls the engine itself uses on item charge.
; Restore only gives back charge that was DAMAGED off: a gun whose stored charge is a hard 0 (drained
; in an earlier session) stays at 0 (verified in game 2026-10-12, Guardian Flintlock Pistol). So each
; step re-reads the charge and falls through: from a hard 0, RightItemCharge took SetActorValue while
; LeftItemCharge ignored it and only took ForceActorValue (same session, same log).
Function SetCharge(Int hand, Float value)
	String av = ChargeAV(hand)
	Float cur = PlayerRef.GetActorValue(av)
	If value > cur
		PlayerRef.RestoreActorValue(av, value - cur)
	ElseIf value < cur
		PlayerRef.DamageActorValue(av, cur - value)
	EndIf
	If Math.Abs(PlayerRef.GetActorValue(av) - value) < 0.01
		Return
	EndIf
	PlayerRef.SetActorValue(av, value)
	Float now = PlayerRef.GetActorValue(av)
	If Math.Abs(now - value) < 0.01
		Debug.Trace("[ZP Flintlock] SetCharge " + av + " " + cur + " -> " + value + " needed SetActorValue")
		Return
	EndIf
	PlayerRef.ForceActorValue(av, value)
	Debug.Trace("[ZP Flintlock] SetCharge " + av + " " + cur + " -> " + value + " SetActorValue left " + now + ", ForceActorValue left " + PlayerRef.GetActorValue(av))
EndFunction

Bool Function IsLoaded(Int hand)
	If hand == 0
		Return loadedL
	EndIf
	Return loadedR
EndFunction

Function SetLoaded(Int hand, Bool b)
	If hand == 0
		loadedL = b
	Else
		loadedR = b
	EndIf
EndFunction

Bool Function IsPending(Int hand)
	If hand == 0
		Return pendingL
	EndIf
	Return pendingR
EndFunction

Function SetPending(Int hand, Bool b)
	If hand == 0
		pendingL = b
	Else
		pendingR = b
	EndIf
EndFunction

Function Dbg(String msg)
	If DebugMode
		Debug.Notification("[Flintlock] " + msg)
		Debug.Trace("[ZP Flintlock] " + msg)
	EndIf
EndFunction
