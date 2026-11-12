Scriptname ZFG_ArcaneFeverWidget extends SKI_WidgetBase
{Zenderal - Arcane Fever Gauge. Feeds the player's Arcane Fever to the round gauge zenderal/arcanefever.swf.

Enderal keeps the fever as the NEGATIVE of actor value LastFlattered (0 down to -100): every SureAI script
reads it as -GetActorValue("LastFlattered") (_00E_ArkanistenfieberEffect, _00E_HeroMenuAlias, ...).

The gauge sits right of the player's Health/Mana bars, and the list draws those with TrueHUD's player widget
(the HUD's own bars are hidden). So two copies of the movie exist:
- one in TrueHUD's movie (menu "TrueHUD"), loaded by this script next to TrueHUD's player widget
  (_root.TrueHUD.TrueHUD_MainVisibilityWidgets), which measures the widget's bars itself;
- SkyUI's HUD widget (this script's SKI_WidgetBase side), which follows Vel'dun's HUD bars and is kept
  hidden while the TrueHUD copy is placed. It is the fallback when TrueHUD or its player widget is off.
The fever is read every UpdateInterval seconds and sent only when it changed (rounded to 0.1).}

Actor Property PlayerRef Auto
{000014:Skyrim.esm}

Float Property UpdateInterval = 0.25 Auto
{Seconds between two fever reads.}

; Layout, as shares of the bar block's height (top of the Health frame to the bottom of the lower row).
; AutoReadOnly on purpose: a save keeps an Auto property's value, so a changed default would never reach it.
; Change them here and recompile.
Float Property RadiusK = 0.64 AutoReadOnly
{Gauge radius.}

Float Property GapK = 0.15 AutoReadOnly
{From the bars' visible arrow tips to the gauge's centre-minus-radius; the gauge's left diamond reaches 0.08 x
radius past that, so the gap you see is (GapK - 0.051) x height: about 0.1 x height (~5 px at 1440p), close but
not touching (curator, 2026-11-12). History: 0.24 then 0.05 measured from TrueHUD's frame bounds, which reach
9.5 units past the visible tips; since build 4 the widget measures the tips themselves.}

Float Property OffsetX = 0.0 AutoReadOnly
{Extra shift right (+) or left (-).}

Float Property OffsetY = 0.0 AutoReadOnly
{Extra shift down (+) or up (-).}

String Property TRUEHUD_MENU = "TrueHUD" AutoReadOnly
String Property TRUEHUD_HOST = "_root.TrueHUD.TrueHUD_MainVisibilityWidgets" AutoReadOnly
String Property TRUEHUD_CLIP = "ZFG_ArcaneFeverGauge" AutoReadOnly
String Property WIDGET_FILE = "exported/widgets/zenderal/arcanefever.swf" AutoReadOnly

; MCM Helper settings (MCM/Config/Zenderal - Arcane Fever Gauge/: config.json + settings.ini defaults; a player's
; changes land in MCM/Settings/Zenderal - Arcane Fever Gauge.ini). The MCM page itself is quest 801
; (ZFG_ArcaneFeverMCM), which calls ApplySettings on every change.
String Property MCM_MOD = "Zenderal - Arcane Fever Gauge" AutoReadOnly

Float _lastSent = -1.0
Int _thState = 0       ; 0 = not loaded, 1 = load requested, 2 = loaded
Int _thWait = 0        ; ticks left before a load request counts as failed
Int _thTries = 0       ; load requests this session (gives up after 5)
Int _tick = 0
Bool _hudSuppressed = False
Int _toggleKey = -1     ; the registered show/hide hotkey (DXScanCode), -1 = none
Bool _autoFade = False
Float _fadeDelay = 5.0
Bool _hidden = False
Float _lastShownAt = 0.0  ; real time of the last fever change or peek (auto-fade bookkeeping)


String Function GetWidgetSource()
	Return "zenderal/arcanefever.swf"
EndFunction

Event OnWidgetInit()
	; The HUD modes Vel'dun's Health and Mana bars show in (HUDMenu.SetModes), so the HUD copy comes and goes with them.
	String[] m = new String[5]
	m[0] = "All"
	m[1] = "StealthMode"
	m[2] = "Swimming"
	m[3] = "HorseMode"
	m[4] = "WarHorseMode"
	Modes = m
EndEvent

Event OnGameReload()
	Parent.OnGameReload()
	; Runs on the first start and on every load (SKI_PlayerLoadGameAlias). The TrueHUD copy does not need
	; SkyUI, so the loop starts here, not in OnWidgetReset.
	_thState = 0
	_thWait = 0
	_thTries = 0
	_tick = 0
	_lastSent = -1.0
	_lastShownAt = Utility.GetCurrentRealTime()
	ApplySettings()
	RegisterForSingleUpdate(1.0)
EndEvent

Event OnWidgetReset()
	Parent.OnWidgetReset()
	UI.InvokeFloatA(HUD_MENU, WidgetRoot + ".setLayout", LayoutArgs())
	UI.InvokeBool(HUD_MENU, WidgetRoot + ".setSuppressed", _hudSuppressed)
	UI.InvokeFloatA(HUD_MENU, WidgetRoot + ".setDisplay", DisplayArgs())
	SendFever(True)
EndEvent

Event OnUpdate()
	If _tick % 4 == 0
		CheckTrueHUD()
	EndIf
	_tick += 1
	SendFever(False)
	RegisterForSingleUpdate(UpdateInterval)
EndEvent

Float[] Function LayoutArgs()
	Float[] a = new Float[4]
	a[0] = RadiusK
	a[1] = GapK
	a[2] = OffsetX
	a[3] = OffsetY
	Return a
EndFunction

String Function TrueHUDRoot()
	Return TRUEHUD_HOST + "." + TRUEHUD_CLIP + ".widget"
EndFunction

; Loads the TrueHUD copy when TrueHUD's menu is open and keeps the HUD copy hidden while it is placed.
Function CheckTrueHUD()
	If !UI.IsMenuOpen(TRUEHUD_MENU)
		_thState = 0
		SetHudSuppressed(False)
		Return
	EndIf
	String root = TrueHUDRoot()
	If UI.GetBool(TRUEHUD_MENU, root + ".zfgReady")
		If _thState != 2
			_thState = 2
			UI.InvokeFloatA(TRUEHUD_MENU, root + ".setLayout", LayoutArgs())
			UI.InvokeFloatA(TRUEHUD_MENU, root + ".setDisplay", DisplayArgs())
			SendFever(True)
		EndIf
		SetHudSuppressed(UI.GetBool(TRUEHUD_MENU, root + ".active"))
		Return
	EndIf
	; Not there (first time, or TrueHUD rebuilt its movie): request a load, then give it time.
	SetHudSuppressed(False)
	If _thState == 1 && _thWait > 0
		_thWait -= 1
		Return
	EndIf
	If _thTries >= 5
		Return
	EndIf
	If UI.GetString(TRUEHUD_MENU, TRUEHUD_HOST + "._name") != "TrueHUD_MainVisibilityWidgets"
		Return
	EndIf
	String[] args = new String[2]
	args[0] = TRUEHUD_CLIP
	args[1] = "16000"
	UI.InvokeStringA(TRUEHUD_MENU, TRUEHUD_HOST + ".createEmptyMovieClip", args)
	UI.InvokeString(TRUEHUD_MENU, TRUEHUD_HOST + "." + TRUEHUD_CLIP + ".loadMovie", WIDGET_FILE)
	_thState = 1
	_thWait = 3
	_thTries += 1
EndFunction

Function SetHudSuppressed(Bool b)
	If b != _hudSuppressed
		_hudSuppressed = b
		If WidgetRoot != ""
			UI.InvokeBool(HUD_MENU, WidgetRoot + ".setSuppressed", b)
		EndIf
	EndIf
EndFunction

Function SendFever(Bool force)
	If PlayerRef == None
		Return
	EndIf
	Float fever = -PlayerRef.GetActorValue("LastFlattered")
	If fever < 0.0
		fever = 0.0
	ElseIf fever > 100.0
		fever = 100.0
	EndIf
	fever = (Math.Floor(fever * 10.0 + 0.5) as Float) / 10.0
	If fever == _lastSent && !force
		Return
	EndIf
	_lastSent = fever
	_lastShownAt = Utility.GetCurrentRealTime()
	If WidgetRoot != ""
		UI.InvokeFloat(HUD_MENU, WidgetRoot + ".setFever", fever)
	EndIf
	If _thState == 2
		UI.InvokeFloat(TRUEHUD_MENU, TrueHUDRoot() + ".setFever", fever)
	EndIf
EndFunction

; ---- display options (MCM) and the show/hide hotkey ----------------------------------------------------------

Float[] Function DisplayArgs()
	Float[] a = new Float[3]
	a[0] = 0.0
	If _autoFade
		a[0] = 1.0
	EndIf
	a[1] = _fadeDelay
	a[2] = 0.0
	If _hidden
		a[2] = 1.0
	EndIf
	Return a
EndFunction

; Reads the MCM settings, (re)registers the hotkey and sends the display options to both copies.
; Called on every load and by ZFG_ArcaneFeverMCM on every setting change.
Function ApplySettings()
	If !MCM.IsInstalled()
		Return
	EndIf
	_autoFade = MCM.GetModSettingBool(MCM_MOD, "bAutoFade:General")
	_fadeDelay = MCM.GetModSettingFloat(MCM_MOD, "fFadeDelay:General")
	If _fadeDelay < 0.5
		_fadeDelay = 5.0
	EndIf
	_hidden = MCM.GetModSettingBool(MCM_MOD, "bHidden:General")
	Int newKey = MCM.GetModSettingInt(MCM_MOD, "iToggleKey:General")
	If newKey != _toggleKey
		If _toggleKey > 0
			UnregisterForKey(_toggleKey)
		EndIf
		_toggleKey = newKey
	EndIf
	If _toggleKey > 0
		RegisterForKey(_toggleKey)
	EndIf
	_lastShownAt = Utility.GetCurrentRealTime()
	PushDisplay()
EndFunction

Function PushDisplay()
	Float[] a = DisplayArgs()
	If WidgetRoot != ""
		UI.InvokeFloatA(HUD_MENU, WidgetRoot + ".setDisplay", a)
	EndIf
	If _thState == 2
		UI.InvokeFloatA(TRUEHUD_MENU, TrueHUDRoot() + ".setDisplay", a)
	EndIf
EndFunction

; Hidden -> show (for the fade delay, if auto-fade is on). Faded out by auto-fade -> show it again for the delay.
; Shown -> hide. The hidden state is saved in the MCM settings, so it holds across saves and shows in the MCM.
Event OnKeyDown(Int keyCode)
	If keyCode != _toggleKey || Utility.IsInMenuMode() || UI.IsTextInputEnabled()
		Return
	EndIf
	Float now = Utility.GetCurrentRealTime()
	If _hidden
		_hidden = False
	ElseIf _autoFade && now - _lastShownAt > _fadeDelay
		; faded out: bring it back for the delay
	Else
		_hidden = True
	EndIf
	_lastShownAt = now
	MCM.SetModSettingBool(MCM_MOD, "bHidden:General", _hidden)
	PushDisplay()
EndEvent
