Scriptname ZEN_ControllerLayout extends ReferenceAlias
{Zenderal - Controller Layout. The file-based binds ship as loose files in this mod; this script
handles the parts that other mods keep IN THE SAVE, where no file can reach them:

  1. Gamepad++ D-pad gestures - written straight into Gamepad++'s key handler, the same fields its
     MCM "Load Preset" fills. Hold = stance, double-tap Left = Quick Light, double-tap Right = Hero Menu.
  2. Quick Light's keyboard key moved from L to K: L is also Enderal's horse-call key. Hold Activate
     (A / E) still casts Quick Light too. (The list has no lantern mod; keybinds.json's SWLToggle is stale.)
  3. B closes Enderal's Hero Menu. Gamepad++ cannot do this (it only sends keys), so this alias
     listens for B and calls the Hero Menu script's own Esc path.

Items 1-2 are written ONCE per save (per LAYOUT_VERSION), so a player's later MCM changes stick.
Bump LAYOUT_VERSION to push a changed layout into existing saves. Every target is looked up by
plugin + FormID and cast, so a missing or changed mod is skipped, never written blindly.}

Int Property LAYOUT_VERSION = 3 AutoReadOnly  ; 2: double-tap Left L -> K (Quick Light); 3: A + D-pad potions

; SKSE key codes
Int Property KEY_ESC = 1 AutoReadOnly
Int Property KEY_K = 37 AutoReadOnly
Int Property PAD_DPAD_UP = 266 AutoReadOnly
Int Property PAD_DPAD_DOWN = 267 AutoReadOnly
Int Property PAD_DPAD_LEFT = 268 AutoReadOnly
Int Property PAD_DPAD_RIGHT = 269 AutoReadOnly
Int Property PAD_A = 276 AutoReadOnly
Int Property PAD_B = 277 AutoReadOnly

; Keys Gamepad++ presses (DirectInput scan codes)
Int Property SEND_QUICK_LIGHT = 37 AutoReadOnly      ; K - Quick Light (set by ApplyQuickLight)
Int Property SEND_HERO_MENU = 35 AutoReadOnly        ; H - Enderal's Hero Menu key
Int Property SEND_STANCE_NEUTRAL = 26 AutoReadOnly   ; [ - Stances.ini stance_neutral_pad
Int Property SEND_STANCE_MID = 43 AutoReadOnly       ; \ - Stances.ini stance_mid_pad (NOT ', No Compass In Dialogue's key)
Int Property SEND_STANCE_HIGH = 27 AutoReadOnly      ; ] - Stances.ini stance_high_pad
Int Property SEND_STANCE_LOW = 39 AutoReadOnly       ; ; - Stances.ini stance_low_pad
; Swift Potion Reborn hotkeys, as Zenderal - Settings Applier's HotkeyData.json sets them
Int Property SEND_POTION_HEALTH = 203 AutoReadOnly   ; Left arrow  - Restore Health
Int Property SEND_POTION_MANA = 200 AutoReadOnly     ; Up arrow    - Restore Mana
Int Property SEND_POTION_STAMINA = 205 AutoReadOnly  ; Right arrow - Restore Stamina

Int Property MAX_TRIES = 8 AutoReadOnly

Int iAppliedVersion = 0
Int iTries = 0

; ---------------------------------------------------------------- lifecycle

Event OnInit()
	Setup()
EndEvent

Event OnPlayerLoadGame()
	Setup()
EndEvent

Function Setup()
	RegisterForKey(PAD_B)
	If iAppliedVersion < LAYOUT_VERSION
		iTries = 0
		; Other mods' aliases initialise a few seconds into a new game; let them finish first.
		; NB the timer pauses while a menu is open (character creation included).
		RegisterForSingleUpdate(15.0)
	EndIf
EndFunction

Event OnUpdate()
	Int gpp = ApplyGamepadPlusPlus()
	ApplyQuickLight()
	If gpp >= 0
		iAppliedVersion = LAYOUT_VERSION
		Debug.Trace("[ZEN_ControllerLayout] layout v" + LAYOUT_VERSION + " applied (Gamepad++ " + gpp + ")")
	Else
		iTries += 1
		If iTries < MAX_TRIES
			RegisterForSingleUpdate(15.0)
		Else
			Debug.Trace("[ZEN_ControllerLayout] Gamepad++ never initialised; giving up until next load")
		EndIf
	EndIf
EndEvent

; ---------------------------------------------------------------- Hero Menu: B closes

Event OnKeyDown(Int KeyCode)
	If KeyCode == PAD_B && UI.IsMenuOpen("CustomMenu")
		Quest levelsystem = Game.GetFormFromFile(0x010AA2, "Skyrim.esm") As Quest
		If levelsystem
			_00E_Game_SkillmenuSC heroMenu = levelsystem.GetAlias(0) As _00E_Game_SkillmenuSC
			If heroMenu
				; Enderal's handler closes only when its own MenuOpen flag is set, so B in any other
				; custom menu is ignored there.
				heroMenu.OnKeyDown(KEY_ESC)
			EndIf
		EndIf
	EndIf
EndEvent

; ---------------------------------------------------------------- Gamepad++
; Returns 1 applied, 0 Gamepad++ not installed (nothing to do), -1 not initialised yet (retry).

Int Function ApplyGamepadPlusPlus()
	Quest q = Game.GetFormFromFile(0x000800, "Gamepad++.esp") As Quest
	If !q
		Return 0
	EndIf
	gpp_keyhandler kh = q.GetAlias(1) As gpp_keyhandler
	If !kh || !kh.aiNonComboActions
		Return -1
	EndIf

	; Action keys = the four D-pad buttons. Combo key 1 = A (as CCS ships it), carrying the potions.
	kh.GPP_KEYCODE_A1 = PAD_DPAD_LEFT
	kh.GPP_KEYCODE_A2 = PAD_DPAD_RIGHT
	kh.GPP_KEYCODE_A3 = PAD_DPAD_UP
	kh.GPP_KEYCODE_A4 = PAD_DPAD_DOWN
	kh.GPP_KEYCODE_C1 = PAD_A
	kh.GPP_KEYCODE_C2 = -1
	kh.GPP_KEYCODE_C3 = -1
	kh.GPP_KEYCODE_C4 = -1
	kh.bFourthComboEnabled = False
	kh.bExtControlsEnabled = False
	kh.bMultiTapEnabled = True
	kh.bLongPressEnabled = True

	; Index = button * 4 + press, button 0 Left 1 Right 2 Up 3 Down,
	; press 0 HOLD, 1 single, 2 double, 3 triple (gpp_keyhandler.OnUpdate: i * 4 + iMultiTap).
	; Single taps stay empty: the engine's own favourites hotkeys 5-8 own a D-pad tap.
	Int[] acts = NewEmptyActions()
	acts[0] = SEND_STANCE_NEUTRAL   ; hold Left
	acts[2] = SEND_QUICK_LIGHT      ; double-tap Left
	acts[4] = SEND_STANCE_MID       ; hold Right
	acts[6] = SEND_HERO_MENU        ; double-tap Right
	acts[8] = SEND_STANCE_HIGH      ; hold Up
	acts[12] = SEND_STANCE_LOW      ; hold Down
	kh.aiNonComboActions = acts
	; Hold A + tap a D-pad button = Swift Potion. Gamepad++ decides single vs double tap after its
	; multi-tap delay (0.3 s), and only counts the combo if A is STILL held then.
	Int[] combo = NewEmptyActions()
	combo[1] = SEND_POTION_HEALTH   ; A + Left
	combo[5] = SEND_POTION_STAMINA  ; A + Right
	combo[9] = SEND_POTION_MANA     ; A + Up
	kh.aiC1Actions = combo
	kh.aiC2Actions = NewEmptyActions()
	kh.aiC3Actions = NewEmptyActions()
	kh.aiC4Actions = NewEmptyActions()

	kh.RegisterKeys()
	Return 1
EndFunction

Int[] Function NewEmptyActions()
	Int[] a = new Int[16]
	Int i = 0
	While i < 16
		a[i] = -1
		i += 1
	EndWhile
	Return a
EndFunction

; ---------------------------------------------------------------- Quick Light

Function ApplyQuickLight()
	Quest q = Game.GetFormFromFile(0x000D62, "QuickLight.esp") As Quest
	If !q
		Return
	EndIf
	aaaQLPlayerAliasScript ql = q.GetAlias(0) As aaaQLPlayerAliasScript
	If ql
		; Default was L, the same key as the lantern and Enderal's horse call. Hold-Activate stays on.
		; (Quick Light's MCM keeps displaying L - its label is a private variable - but K is live.)
		ql.SetLightKey(KEY_K)
	EndIf
EndFunction
