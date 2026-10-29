Scriptname ZP_ProphecyMenu extends Quest
{The Prophecy perk menu: B612's traits card menu (b612.esp 0x803, the menu Biggie Traits uses), one card per perk with
a thumbnail from Interface/ProphecyPics/<EditorID>.dds. Skyrim's perk screen (what Custom Skills Framework draws on)
does not work in Enderal 2.1 - see arch-docs/patches/Prophecy.md.
Flow: tree choice (message box) -> the tree's five cards (learned / locked / available) -> pick up to as many as you
have points; picks are applied in tree order, so a root and its branch can be taken together.
Arrays are tree-major; tree t's perks are TreeStart[t] .. TreeStart[t+1]-1; ParentA/ParentB hold the indices of the perk(s) that unlock a node (either one
is enough), -1 for none. All filled by src/Prophecy/tools/01-build-trees.py.
Point award (one every 3 levels, 30 at level 90; LevelsPerPoint and MaxPoints are unused) first followed Subclasses of Skyrim 2's
dar_sostreescript.PerkIncrease (Darenii).}

Message Property ZP_ProphecyMenuMsg Auto
GlobalVariable Property ZP_ProphecyPoints Auto
GlobalVariable Property ZP_ProphecyPointsEarned Auto
Perk[] Property Perks Auto
String[] Property Descriptions Auto
String[] Property Images Auto
Int[] Property ParentA Auto
Int[] Property ParentB Auto
Int[] Property PowerPerk Auto      ; perks whose ability is a power: AddPerk alone does not grant it
Form[] Property PowerSpell Auto     ; a Spell (power) or a Shout (Gap Closer)
Int[] Property TreeStart Auto       ; one entry per tree + a final total
Int[] Property GiftPerk Auto        ; perk index -> GiftItem, handed out once per save
Form[] Property GiftItem Auto
Int[] Property LevelReq Auto        ; per perk: the player level it needs (capstones: 30, curator 2026-10-25), 0 for none
Bool[] giftDone
Int Property LevelsPerPoint = 5 Auto
Int Property MaxPoints = 30 Auto   ; unused: saves keep the value they started with (20), see PointsDueAt

Bool busy
Bool openAfterFirstPoint   ; set when point #1 is paid: open Prophecy once its prompt (and any other box) closes
Bool ledgerRepairedV3
Bool granting

; Called by the Prophecy power with the arrays from the current plugin (the effect is created fresh on every cast).
; The values above are only what the quest started with in this save; this keeps existing saves current when a
; perk is added. Skipped while the menu is up, so the arrays never change under it.
Function Refresh(Perk[] akPerks, String[] asDescriptions, String[] asImages, Int[] aiParentA, Int[] aiParentB, Int[] aiPowerPerk, Form[] akPowerSpell, Int[] aiTreeStart, Int[] aiGiftPerk, Form[] akGiftItem, Int[] aiLevelReq)
	If busy
		Return
	EndIf
	Perks = akPerks
	Descriptions = asDescriptions
	Images = asImages
	ParentA = aiParentA
	ParentB = aiParentB
	PowerPerk = aiPowerPerk
	PowerSpell = akPowerSpell
	TreeStart = aiTreeStart
	GiftPerk = aiGiftPerk
	GiftItem = akGiftItem
	LevelReq = aiLevelReq
	; Past 128 talents (Rage, 2026-10-27) the property arrays are larger than a Papyrus "new" array may be; they are
	; built by the VM from the plugin, which should not be limited - this says so in game if it is.
	Int total = TreeStart[TreeStart.Length - 1]
	If Perks.Length != total || Descriptions.Length != total || ParentA.Length != total || LevelReq.Length != total
		Debug.Trace("Prophecy: talent arrays truncated - Perks " + Perks.Length + ", Descriptions " + Descriptions.Length + ", ParentA " + ParentA.Length + ", LevelReq " + LevelReq.Length + ", expected " + total, 2)
		Debug.MessageBox("Prophecy: the talent list was cut short (" + Perks.Length + " of " + total + "). Please report this.")
	EndIf
EndFunction

; New saves listen for level-ups from the start. Saves older than the prompts are hooked by ZP_ProphecyLevelWatch
; (0x80E), which calls WatchLevelUps when the save loads.
Event OnInit()
	RegisterForMenu("MessageBoxMenu")
EndEvent

; Called by ZP_ProphecyLevelWatch on quest start and every load: (re)registers the listener and pays any point the
; save is already owed, with its prompt.
Function WatchLevelUps()
	RegisterForMenu("MessageBoxMenu")
	If busy || granting
		Return
	EndIf
	granting = True
	AwardPoints()
	granting = False
EndFunction

; Called by the Prophecy power. Runs on this quest so the menus outlive the power's instant magic effect.
Function RequestOpen()
	If !busy
		RegisterForSingleUpdate(0.1)
	EndIf
EndFunction

Event OnUpdate()
	If busy
		; second thread while the card menu is up (scheduled from ShowTree): hide B612's Random button
		HideRandomButton()
		Return
	EndIf
	busy = True
	AwardPoints()
	openAfterFirstPoint = False    ; the menu is opening anyway
	RepairPowers()
	GiveGifts(True)
	; Prophecy v3: ZenProphecyUI.dll draws the trees as constellations (SKSE Menu Framework window) and asks for each
	; perk with the mod event ZP_ProphecyLearn (numArg = the perk's index in these arrays); learning stays TryLearn.
	If SKSE.GetPluginVersion("ZenProphecyUI") > 0
		RegisterForModEvent("ZP_ProphecyLearn", "OnProphecyLearn")
		SendModEvent("ZP_ProphecyUI_Open")
		busy = False
		Return
	EndIf
	Int tree = 0
	While tree >= 0
		Debug.Notification("Prophecy points: " + ZP_ProphecyPoints.GetValueInt())
		tree = ZP_ProphecyMenuMsg.Show()
		If tree >= 0 && tree < TreeStart.Length - 1
			ShowTree(tree)
		Else
			tree = -1
		EndIf
	EndWhile
	busy = False
EndEvent

; Called on opening the menu and whenever a message box closes outside it (Enderal's level-up box closes, then
; _00E_EPUpdateFunctions.levelUp calls Game.SetPlayerLevel): grants each newly reached point level with its prompt.
Function AwardPoints()
	BindGlobals()
	RegisterForMenu("MessageBoxMenu")
	Int level = Game.GetPlayer().GetLevel()
	Int due = PointsDueAt(level)
	If !ledgerRepairedV3
		RepairLedger(due)
	EndIf
	Int earned = ZP_ProphecyPointsEarned.GetValueInt()
	; the point-gained sound (curator's, 2026-10-25), looked up by ID: a running quest keeps the property values it
	; started with in a save, so a new property would stay empty on existing saves (see BindGlobals)
	; and Enderal's own "memory streams into you" wisps (_00E_Class_MemoryAbsorbFXS, what _00E_Class_PerkScript plays
	; when a talent is learned in the meditation space). Both run BEFORE the prompt: a message box pauses the game,
	; which would freeze them behind it.
	Sound pointSound = None
	EffectShader flourish = None
	If earned < due
		pointSound = Game.GetFormFromFile(0x9B1, "Zenderal - Prophecy.esp") as Sound   ; ZP_Prophecy_PointGainedMarker
		flourish = Game.GetFormFromFile(0x0ACDC5, "Skyrim.esm") as EffectShader          ; _00E_Class_MemoryAbsorbFXS
	EndIf
	While earned < due
		earned += 1
		ZP_ProphecyPoints.SetValue(ZP_ProphecyPoints.GetValueInt() + 1)
		ZP_ProphecyPointsEarned.SetValue(earned)
		If earned == 1
			openAfterFirstPoint = True   ; curator, 2026-10-25: the first point shows you where to spend it
		EndIf
		Actor player = Game.GetPlayer()
		If pointSound
			pointSound.Play(player)
		EndIf
		If flourish
			flourish.Play(player)
			Utility.Wait(2.5)
			flourish.Stop(player)
		EndIf
		Debug.MessageBox(PointText(earned) + "\n\nYou gained a Prophecy point (level " + PointLevel(earned) + "). Cast Prophecy to spend it.")
	EndWhile
	Debug.Trace("ZP_ProphecyMenu: level " + level + ", due " + due + ", earned " + earned + ", points " + ZP_ProphecyPoints.GetValueInt())
EndFunction

; Point levels (curator, 2026-10-25): one every 3 levels, 30 by level 90 (each tree has 11 talents since then).
; Was 5, 10, 15, 20, 30, then every 5, capped at 20. The cap is a literal: a running quest keeps the MaxPoints it
; started with in a save (20), so the property cannot raise it.
Int Function PointsDueAt(Int level)
	Int due = level / 3
	If due > 30
		due = 30
	EndIf
	Return due
EndFunction

; the level that pays point n (1-based)
Int Function PointLevel(Int n)
	Return n * 3
EndFunction

String Function PointText(Int n)
	; curator's "memories in the mist" voice, 2026-10-24: one line per milestone to level 30, then three in turn
	If n == 1
		Return "Memories flood your mind, and in the mist you see a vision: a figure standing where you stand, wearing your face, looking back at you. Then it is gone, and something of it remains."
	ElseIf n == 2
		Return "The mist returns, thinner now. Through it you glimpse moments that have not happened yet, sharp as old memories and just as impossible to forget."
	ElseIf n == 3
		Return "You close your eyes and the vision is already waiting. You walk a road you have never travelled, and you know every stone of it."
	ElseIf n == 4
		Return "Memories that are not yours press in, the lives of those who walked this path before you. In the mist they turn and, one by one, step aside."
	ElseIf n == 5
		Return "There is no mist anymore. The vision stands clear before you, and you understand that it was never showing you the future. It was showing you yourself."
	ElseIf n % 3 == 0
		Return "Another memory surfaces from the mist, as if it had always been waiting for you."
	ElseIf n % 3 == 1
		Return "For a heartbeat the world falls silent, and in the mist a vision shows you one more step of the path."
	EndIf
	Return "The mist parts briefly. What you see there, you will carry with you."
EndFunction

Event OnMenuClose(String asMenuName)
	If busy || granting || asMenuName != "MessageBoxMenu"
		Return
	EndIf
	If openAfterFirstPoint
		; the first point's prompt (or a box after it) has closed: wait out any box still queued, then open Prophecy
		Utility.Wait(0.3)
		While UI.IsMenuOpen("MessageBoxMenu")
			Utility.Wait(0.3)
		EndWhile
		If openAfterFirstPoint
			openAfterFirstPoint = False
			RequestOpen()
			Return
		EndIf
	EndIf
	granting = True
	Utility.Wait(0.5)    ; the level-up box closes before Game.SetPlayerLevel runs
	AwardPoints()
	granting = False
EndEvent

; A running quest keeps the property values it started with in a save, so a save whose quest started before
; ZP_ProphecyPointsEarned (0x809) existed has it as None - "earned" read 0 and every opening re-awarded every point.
Function BindGlobals()
	If !ZP_ProphecyPoints
		ZP_ProphecyPoints = Game.GetFormFromFile(0x802, "Zenderal - Prophecy.esp") as GlobalVariable
	EndIf
	If !ZP_ProphecyPointsEarned
		ZP_ProphecyPointsEarned = Game.GetFormFromFile(0x809, "Zenderal - Prophecy.esp") as GlobalVariable
	EndIf
EndFunction

; Once per save: "earned" becomes what the save was really given (balance + learned perks, each perk cost a point),
; capped at what the level is due, so AwardPoints then hands out the rest with its prompts. A balance above
; due - learned (the unbound-counter bug, cheats, the 2026-10-24 point-level change) is lowered. The first version
; (V2) marked due as earned without paying it, so a save that first opened the menu at level 5+ lost its points
; (testers, level 6, 0 points); ledgerRepairedV3 repairs saves that ran it.
Function RepairLedger(Int due)
	Actor player = Game.GetPlayer()
	Int learned = 0
	Int i = 0
	While i < Perks.Length
		If Perks[i] && player.HasPerk(Perks[i])
			learned += 1
		EndIf
		i += 1
	EndWhile
	Int points = ZP_ProphecyPoints.GetValueInt()
	Int given = points + learned
	If given > due
		Int fair = due - learned
		If fair < 0
			fair = 0
		EndIf
		ZP_ProphecyPoints.SetValue(fair)
		Debug.Notification("Prophecy points corrected: " + points + " -> " + fair)
		given = due
	EndIf
	ZP_ProphecyPointsEarned.SetValue(given)
	Debug.Trace("ZP_ProphecyMenu: ledger repaired - due " + due + ", learned " + learned + ", points " + points + " -> " + ZP_ProphecyPoints.GetValueInt() + ", earned " + given)
	ledgerRepairedV3 = True
EndFunction

Function ShowTree(Int tree)
	b612_TraitsMenu menu = Game.GetFormFromFile(0x803, "b612.esp") as b612_TraitsMenu
	If !menu
		Debug.Notification("Prophecy needs B612 (b612.esp).")
		Return
	EndIf
	Actor player = Game.GetPlayer()
	Int start = TreeStart[tree]
	Int count = TreeStart[tree + 1] - start
	Bool again = True
	While again
		again = False
		menu.Init()
		Int i = 0
		While i < count
			Int idx = start + i
			String title = Perks[idx].GetName()
			If player.HasPerk(Perks[idx])
				title = title + " - Learned"
			ElseIf player.GetLevel() < LevelNeeded(idx)
				title = title + " - Level " + LevelNeeded(idx)
			EndIf
			; the talent's name heads its description, one line break (Papyrus "\n" = a lone LF; a CRLF stored in the
			; plugin showed as a double break in B612's plain-text field, curator 2026-10-24)
			menu.AddItem(title, Perks[idx].GetName() + "\n" + Descriptions[idx], Images[idx])
			i += 1
		EndWhile
		Int maxPick = ZP_ProphecyPoints.GetValueInt()
		If maxPick < 1
			maxPick = 1
		ElseIf maxPick > count
			maxPick = count
		EndIf
		HideRandomButton()
		RegisterForSingleUpdate(0.25)   ; and again once the menu has rendered
		String[] picked = menu.Show(aiMaxSelection = maxPick, aiMinSelection = 0)

		; apply in tree order so a parent picked together with its child is learned first
		Bool[] want = new Bool[16]   ; a tree's talents (11 since 2026-10-25; this was 8 and dropped picks 9-11)
		i = 0
		While picked && i < picked.Length
			Int k = picked[i] as Int
			If k >= 0 && k < count
				want[k] = True
			EndIf
			i += 1
		EndWhile
		String refused = ""
		i = 0
		While i < count
			If want[i]
				Int idx = start + i
				If !player.HasPerk(Perks[idx]) && !Unlocked(idx)
					refused = refused + Perks[idx].GetName() + ": learn " + RequirementText(idx) + " first.\n"
				ElseIf !player.HasPerk(Perks[idx]) && player.GetLevel() < LevelNeeded(idx)
					refused = refused + Perks[idx].GetName() + ": reach level " + LevelNeeded(idx) + " first.\n"
				Else
					TryLearn(idx)
				EndIf
			EndIf
			i += 1
		EndWhile
		If refused != ""
			Debug.MessageBox(refused)
			Utility.Wait(0.1)
			While UI.IsMenuOpen("MessageBoxMenu")
				Utility.Wait(0.1)
			EndWhile
			again = True
		EndIf
	EndWhile
EndFunction

Function HideRandomButton()
	UI.SetBool("CustomMenu", "_root.Traits_mc.RandomBtn_mc._visible", False)
	UI.SetBool("CustomMenu", "_root.Traits_mc.RandomBtn_mc.disabled", True)
EndFunction

; Prophecy v3's window: a click on a lit node, after its confirm box.
Event OnProphecyLearn(String asEventName, String asStrArg, Float afNumArg, Form akSender)
	Int idx = afNumArg as Int
	If busy || idx < 0 || idx >= Perks.Length
		Return
	EndIf
	TryLearn(idx)
EndEvent

Function TryLearn(Int idx)
	Actor player = Game.GetPlayer()
	If player.HasPerk(Perks[idx])
		Return
	ElseIf !Unlocked(idx)
		Debug.Notification(Perks[idx].GetName() + " requires " + RequirementText(idx) + ".")
	ElseIf player.GetLevel() < LevelNeeded(idx)
		Debug.Notification(Perks[idx].GetName() + " requires level " + LevelNeeded(idx) + ".")
	ElseIf ZP_ProphecyPoints.GetValueInt() < 1
		Debug.Notification("No Prophecy points for " + Perks[idx].GetName() + ". You gain one every 3 levels.")
	Else
		player.AddPerk(Perks[idx])
		GrantPower(idx)
		GiveGifts(True)
		ZP_ProphecyPoints.SetValue(ZP_ProphecyPoints.GetValueInt() - 1)
		Debug.Notification("Learned " + Perks[idx].GetName() + ".")
	EndIf
EndFunction

Bool Function Unlocked(Int idx)
	If ParentA[idx] < 0
		Return True
	EndIf
	Actor player = Game.GetPlayer()
	If player.HasPerk(Perks[ParentA[idx]])
		Return True
	EndIf
	Return ParentB[idx] >= 0 && player.HasPerk(Perks[ParentB[idx]])
EndFunction

; LevelReq is None on a save until the Prophecy power's first Refresh after the 2026-10-25 update - then nothing is gated
Int Function LevelNeeded(Int idx)
	If LevelReq && idx < LevelReq.Length
		Return LevelReq[idx]
	EndIf
	Return 0
EndFunction

String Function RequirementText(Int idx)
	String t = Perks[ParentA[idx]].GetName()
	If ParentB[idx] >= 0
		t = t + " or " + Perks[ParentB[idx]].GetName()
	EndIf
	Return t
EndFunction

Function GrantPower(Int idx)
	Int k = 0
	While k < PowerPerk.Length
		If PowerPerk[k] == idx
			Give(PowerSpell[k], True)
		EndIf
		k += 1
	EndWhile
EndFunction

; perks learned before powers were granted explicitly get their power back
Function RepairPowers()
	Int k = 0
	While k < PowerPerk.Length
		If Game.GetPlayer().HasPerk(Perks[PowerPerk[k]])
			Give(PowerSpell[k], False)
		EndIf
		k += 1
	EndWhile
EndFunction

; a power is added like any spell; a shout also needs its word taught and unlocked (as Enderal does for its talents)
Function Give(Form f, Bool abVerbose)
	Actor player = Game.GetPlayer()
	If player.HasSpell(f)
		Return
	EndIf
	Shout sh = f as Shout
	If sh
		; a talent that used to be a lesser power (Ice Shot until 2026-10-28) leaves its spell behind in the save
		Spell old = sh.GetNthSpell(0)
		If old && player.HasSpell(old)
			player.RemoveSpell(old)
		EndIf
		Int k = 0
		WordOfPower w = sh.GetNthWordOfPower(0)
		While w      ; every word: Veil Wyrm has three
			Game.TeachWord(w)
			Game.UnlockWord(w)
			k += 1
			w = sh.GetNthWordOfPower(k)
		EndWhile
		player.AddShout(sh)
		If abVerbose
			Debug.Notification("Talent learned: " + sh.GetName())
		EndIf
	Else
		player.AddSpell(f as Spell, abVerbose)
	EndIf
EndFunction

; one-time items for owned perks (Clockwork Turret's turret). giftDone lives in the save, so a turret that is later
; destroyed is replaced only by crafting, never by reopening Prophecy.
Function GiveGifts(Bool abVerbose)
	If !giftDone
		giftDone = new Bool[16]
	EndIf
	Int k = 0
	While k < GiftPerk.Length
		If !giftDone[k] && Game.GetPlayer().HasPerk(Perks[GiftPerk[k]])
			giftDone[k] = True
			Game.GetPlayer().AddItem(GiftItem[k], 1, !abVerbose)
		EndIf
		k += 1
	EndWhile
EndFunction
