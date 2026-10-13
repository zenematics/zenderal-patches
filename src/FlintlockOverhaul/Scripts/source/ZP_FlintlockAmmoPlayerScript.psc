Scriptname ZP_FlintlockAmmoPlayerScript extends ReferenceAlias
{Zenderal - Flintlock Overhaul. A Gentleman's Flintlock Armoury's pistols are staves, so their
"ammo" is enchantment charge. This script owns that charge on the PLAYER's pistols:
  - a pistol in hand is either LOADED (charge = max) or EMPTY (charge = 0), tracked here;
  - firing empties it, and 2 s later one Flintlock Bullet is taken to load it again;
  - equipping a pistol ignores its stored charge and loads it from a bullet;
  - unequipping a loaded pistol gives the bullet back;
  - charge added by a soul gem in the inventory menu is removed again.
Also adds the hidden perk that scales shot damage like a bow.
NPCs are untouched.}

Actor Property PlayerRef Auto
FormList Property ZP_FlintlockWeapons Auto
MiscObject Property ZP_FlintlockBullet Auto
Perk Property ZP_FlintlockArcheryScaling Auto  ; shot damage scales with Archery + bow talents
Float Property ReloadDelay = 2.0 Auto
Bool Property DebugMode = False AutoReadOnly  ; ReadOnly: not stored in saves, so flipping it takes effect everywhere

; Hand 0 = left, 1 = right (SKSE's WornObject / OnActorAction slot numbering)
Weapon wepL
Weapon wepR
Bool loadedL
Bool loadedR
Bool pendingL
Bool pendingR

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
	Sync()
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
	Dbg("fired hand " + slot + " (source " + source + "), charge now " + GetCharge(slot) + "/" + MaxCharge(slot))
	SetCharge(slot, 0.0)
	SetLoaded(slot, False)
	SetPending(slot, True)
	RegisterForSingleUpdate(ReloadDelay)
EndEvent

Event OnUpdate()
	Int hand = 0
	While hand < 2
		If IsPending(hand)
			SetPending(hand, False)
			TryLoad(hand)
		EndIf
		hand += 1
	EndWhile
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
	SetCharge(hand, MaxCharge(hand))
	SetLoaded(hand, True)
	Dbg("loaded hand " + hand + ", charge now " + GetCharge(hand) + "/" + MaxCharge(hand))
EndFunction

; ---------------------------------------------------------------- helpers

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
