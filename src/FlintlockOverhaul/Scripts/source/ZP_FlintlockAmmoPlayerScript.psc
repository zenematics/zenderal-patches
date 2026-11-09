Scriptname ZP_FlintlockAmmoPlayerScript extends ReferenceAlias
{Zenderal - Flintlock Overhaul. A Gentleman's Flintlock Armoury's pistols are staves, so their
"ammo" is enchantment charge. This script owns that charge on the PLAYER's pistols:
  - a pistol in hand is either LOADED (charge = max) or EMPTY (charge = 0), tracked here;
  - firing empties it; it loads again from one Flintlock Bullet when the player reloads it (below);
  - equipping a pistol ignores its stored charge and loads it from a bullet, unless it was put away fired and not
    reloaded (2026-11-03: it stays empty out of the hand, Sync);
  - unequipping a loaded pistol gives the bullet back;
  - charge added by a soul gem in the inventory menu is removed again.
Also adds the hidden perk that scales shot damage like a bow.
Prophecy's pistol talents (2026-11-01), looked up by FormID so this plugin does not master Prophecy: while Fan the
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
the other pistol fires or reloads (one reload at a time), within DRY_LOCK of the last request, or holstered. A shield in
the other hand (2026-11-03) has its reload too (Pistol Ramrod Reload slings it on the back; shields are left-hand only,
so a right-hand gun), and a torch (2026-11-05; curator: with a torch the gun "would allow pistols to constantly fire with
no reload", the timer below): Pistol Ramrod Reload lowers it into the belt for the reload and takes it back up. A
spell in the other hand (2026-11-07; a player: the gun reloaded "there's just no animation") too, either hand: the
spell hand loads and rams. Elsewhere (mounted, no Pandora rerun) the same press clicks and starts ReloadDelay's timer:
until 2026-11-03 that timer ran from the shot, so with a shield the gun reloaded itself and fired every 2 s with no
reload (curator). Fan the Hammer still reloads by its own timer from the shot. Per hand.
NPCs are untouched.}

Actor Property PlayerRef Auto
FormList Property ZP_FlintlockWeapons Auto
MiscObject Property ZP_FlintlockBullet Auto
Perk Property ZP_FlintlockArcheryScaling Auto  ; shot damage scales with Archery + bow talents
Float Property ReloadDelay = 2.0 Auto
Float Property FanDelay = 0.1 AutoReadOnly
Float Property BladeReloadCooldown = 15.0 AutoReadOnly   ; Prophecy's PISTOL['BladeReloadCooldown'] (its text)
String Property ProphecyPlugin = "Zenderal - Prophecy.esp" AutoReadOnly
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
Int Property TYPE_SHIELD = 10 AutoReadOnly
Int Property TYPE_TORCH = 11 AutoReadOnly
Int Property TYPE_SPELL = 9 AutoReadOnly

; Hand 0 = left, 1 = right (SKSE's WornObject / OnActorAction slot numbering)
Weapon wepL
Weapon wepR
Bool loadedL
Bool loadedR
Bool pendingL
Bool pendingR
MagicEffect fanEffect
Float lastBladeReload = -1000.0   ; real time of Blade and Barrel's last reload
Int holsterL        ; holsters started, per hand
Int holsterR
Float holsterUntilL ; real time the latest holster on that hand ends (0: none; reset on load, real time restarts)
Float holsterUntilR
Float loadAtL       ; real time a fired gun loads by timer (0: no timer)
Float loadAtR
Weapon[] stowedGuns ; fired pistols put away before their reload, by base form ...
Int[] stowedCounts  ; ... and how many of it (two of the same pistol are told apart only by number)
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
	If !stowedGuns
		stowedGuns = new Weapon[64]
		stowedCounts = new Int[64]
	EndIf
	fanEffect = None
	lastBladeReload = -1000.0     ; real time starts again with every game launch
	holsterUntilL = 0.0           ; ... so a saved holster's end means nothing now (repaired below)
	holsterUntilR = 0.0
	loopKeyword = None
	If Game.GetModByName(LoopPlugin) != 255 && Game.GetModByName(ReloadPlugin) != 255
		loopKeyword = Game.GetFormFromFile(LOOP_KEYWORD_ID, LoopPlugin) as Keyword
	EndIf
	; a gun fired before the save: its timer is gone with the old session's real time, so it waits for the attack
	; button, as when its reload is cut short
	Int pend = 0
	While pend < 2
		SetLoadAt(pend, 0.0)
		pend += 1
	EndWhile
	ScheduleLoad()
	If Game.GetModByName(ProphecyPlugin) != 255
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
	If fanEffect && PlayerRef.HasMagicEffect(fanEffect)
		SetLoadAt(slot, Utility.GetCurrentRealTime() + FanDelay)   ; Fan the Hammer: by timer, no animation
	Else
		SetLoadAt(slot, 0.0)         ; the attack button reloads it: its clip, or its timer where none plays
	EndIf
	ScheduleLoad()
EndEvent

; That hand's attack on its empty gun: a click, and the reload asked for (its clip), or its timer started where no clip
; plays (decided at the press: what the other hand holds now)
Event OnControlDown(String control)
	Int hand = 1
	If control == "Left Attack/Block"
		hand = 0
	ElseIf control != "Right Attack/Block"
		Return
	EndIf
	Weapon gun = WeaponIn(hand)
	If Utility.IsInMenuMode() || !IsPending(hand) || !IsPistol(gun) || LoadAt(hand) > 0.0
		Return                       ; nothing to reload, or its timer already runs
	EndIf
	If !AnimatedReload(hand, gun)
		SetLoadAt(hand, Utility.GetCurrentRealTime() + CurrentDelay())
		If dryClick
			dryClick.Play(PlayerRef)
		EndIf
		ScheduleLoad()
		Dbg("hand " + hand + " empty: reloading by timer (no reload clip here)")
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
	If fanEffect && PlayerRef.HasMagicEffect(fanEffect)    ; Fan the Hammer reloads by its own timer, no clip
		Return False
	EndIf
	Int other = 1 - slot
	Int t = PlayerRef.GetEquippedItemType(other)
	If t >= 0 && t <= 4                 ; empty, or a one-handed melee weapon (sheathed for the reload)
		Return True
	ElseIf t == TYPE_SHIELD             ; slung on the back for the reload (left-hand only: the right gun's clips)
		Return slot == 1
	ElseIf t == TYPE_TORCH              ; into the belt for the reload (left-hand only: the right gun's clips)
		Return slot == 1
	ElseIf t == TYPE_SPELL              ; the spell hand loads and rams (either hand)
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

Float Function LoadAt(Int hand)
	If hand == 0
		Return loadAtL
	EndIf
	Return loadAtR
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
; A fired pistol stays empty out of the hand (2026-11-03, curator: unequipping and equipping it again skipped the
; reload): it is kept in stowedGuns, and taken up again it waits for the attack button like after a shot. Both hands'
; outgoing pistols are put away before either incoming one is looked at, so an empty gun moved to the other hand in one
; go stays empty.
Function Sync()
	Weapon nowL = WeaponIn(0)
	Weapon nowR = WeaponIn(1)
	Bool changedL = nowL != wepL
	Bool changedR = nowR != wepR
	Int hand = 0
	While hand < 2
		Weapon was = wepL
		Bool changed = changedL
		If hand == 1
			was = wepR
			changed = changedR
		EndIf
		If changed
			If IsPistol(was) && IsLoaded(hand)
				PlayerRef.AddItem(ZP_FlintlockBullet, 1, True)
			ElseIf IsPistol(was) && IsPending(hand)
				StowEmpty(was)
			EndIf
			SetLoaded(hand, False)
			SetPending(hand, False)
			SetLoadAt(hand, 0.0)
		EndIf
		hand += 1
	EndWhile
	wepL = nowL
	wepR = nowR
	hand = 0
	While hand < 2
		Weapon now = nowL
		Bool changed = changedL
		If hand == 1
			now = nowR
			changed = changedR
		EndIf
		If changed && IsPistol(now)
			; the ones of its form out of both hands before it came in: not the other hand's if that one was in hand
			; already, or came in just before it (the left is looked at first). With the same pistol in both hands
			; coming in together, the left counted the right's as in hand and took the only empty one: the right then
			; loaded (curator 2026-11-03, after a musket swap: "the right hand pistol is always loaded")
			Int pool = PlayerRef.GetItemCount(now)
			If (hand == 0 && nowR == now && !changedR) || (hand == 1 && nowL == now)
				pool -= 1
			EndIf
			SetCharge(hand, 0.0)
			If TakeEmpty(now, pool)
				SetPending(hand, True)       ; loaded by the attack button, as after a shot (OnControlDown)
				Dbg("hand " + hand + " took up an empty pistol: fire to reload")
			Else
				TryLoad(hand)
			EndIf
		EndIf
		hand += 1
	EndWhile
EndFunction

; A fired, unloaded pistol leaves the hand
Function StowEmpty(Weapon w)
	Int i = stowedGuns.Find(w)
	If i < 0
		i = stowedGuns.Find(None)
		If i < 0
			Return                           ; 64 kinds of empty pistol put away: this one is forgotten
		EndIf
		stowedGuns[i] = w
		stowedCounts[i] = 0
	EndIf
	stowedCounts[i] = stowedCounts[i] + 1
	Debug.Trace("[ZP Flintlock] put away empty: " + w + " (" + stowedCounts[i] + " of its form)")
EndFunction

; The pistol just taken in hand is an empty one: every one of its form in the `pool` it came from (the player's out of
; both hands, Sync) is (the engine does not say which it took, so a loaded one is assumed while there is any). Counts
; are capped by the pool (one sold or dropped counts as a loaded one gone).
Bool Function TakeEmpty(Weapon w, Int pool)
	Int i = stowedGuns.Find(w)
	If i < 0
		Return False
	EndIf
	Int empty = stowedCounts[i]
	If empty > pool
		empty = pool
	EndIf
	Bool taken = empty > 0 && empty >= pool
	Debug.Trace("[ZP Flintlock] taken up " + w + ": " + empty + " of " + pool + " out of hand empty, this one " + taken)
	If taken
		empty -= 1
	EndIf
	If empty > 0
		stowedCounts[i] = empty
	Else
		stowedGuns[i] = None
		stowedCounts[i] = 0
	EndIf
	Return taken
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
