Scriptname ZP_ProphecyMenu extends Quest
{The Prophecy perk menu: B612's traits card menu (b612.esp 0x803, the menu Biggie Traits uses), one card per perk with
a thumbnail from Interface/ProphecyPics/<EditorID>.dds. Skyrim's perk screen (what Custom Skills Framework draws on)
does not work in Enderal 2.1 - see arch-docs/patches/Prophecy.md.
Flow: tree choice (message box) -> the tree's five cards (learned / locked / available) -> pick up to as many as you
have points; picks are applied in tree order, so a root and its branch can be taken together.
Arrays are tree-major; tree t's perks are TreeStart[t] .. TreeStart[t+1]-1; ParentA/ParentB hold the indices of the perk(s) that unlock a node (either one
is enough), -1 for none. All filled by src/Prophecy/tools/01-build-trees.py.
Point award (1 per LevelsPerPoint levels, capped at MaxPoints) follows Subclasses of Skyrim 2's
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
Bool[] giftDone
Int Property LevelsPerPoint = 5 Auto
Int Property MaxPoints = 20 Auto

Bool busy

; Called by the Prophecy power with the arrays from the current plugin (the effect is created fresh on every cast).
; The values above are only what the quest started with in this save; this keeps existing saves current when a
; perk is added. Skipped while the menu is up, so the arrays never change under it.
Function Refresh(Perk[] akPerks, String[] asDescriptions, String[] asImages, Int[] aiParentA, Int[] aiParentB, Int[] aiPowerPerk, Form[] akPowerSpell, Int[] aiTreeStart, Int[] aiGiftPerk, Form[] akGiftItem)
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
	RepairPowers()
	GiveGifts(True)
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

Function AwardPoints()
	Int due = Game.GetPlayer().GetLevel() / LevelsPerPoint
	If due > MaxPoints
		due = MaxPoints
	EndIf
	Int earned = ZP_ProphecyPointsEarned.GetValueInt()
	If due > earned
		ZP_ProphecyPoints.SetValue(ZP_ProphecyPoints.GetValueInt() + due - earned)
		ZP_ProphecyPointsEarned.SetValue(due)
		Debug.Notification("Prophecy points gained: " + (due - earned))
	EndIf
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
			EndIf
			menu.AddItem(title, Descriptions[idx], Images[idx])
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
		Bool[] want = new Bool[8]
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

Function TryLearn(Int idx)
	Actor player = Game.GetPlayer()
	If player.HasPerk(Perks[idx])
		Return
	ElseIf !Unlocked(idx)
		Debug.Notification(Perks[idx].GetName() + " requires " + RequirementText(idx) + ".")
	ElseIf ZP_ProphecyPoints.GetValueInt() < 1
		Debug.Notification("No Prophecy points for " + Perks[idx].GetName() + ". You gain one every " + LevelsPerPoint + " levels.")
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
		WordOfPower w = sh.GetNthWordOfPower(0)
		Game.TeachWord(w)
		Game.UnlockWord(w)
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
