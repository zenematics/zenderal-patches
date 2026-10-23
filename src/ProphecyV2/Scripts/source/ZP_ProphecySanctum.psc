Scriptname ZP_ProphecySanctum extends Quest
{Prophecy v2 - the physical sanctum. Modelled on Enderal's meditation (_00E_Class_OpenClassMenuScript: save the
real-world position on a marker, flash + sound, move the player in; the same power brings them back) and on its
walk-up perk nodes (_00E_Class_PerkScript: a message box, then the star glows, the lines light and the memory streams
into the player). Our own copy so the cost is Prophecy points, not Enderal's Memory Points.
Arrays are tree-major (trees of 5 perks, Glory of 4). Lines are the tree edges, LineFrom/LineTo = perk indices.
Stars/lines are re-lit on every entry, so perks learned anywhere else (e.g. the v1 menu) show too.
All properties are filled by src/ProphecyV2/tools/01-build-v2.py.}

Actor Property PlayerRef Auto
ObjectReference Property SanctumOrigin Auto
ObjectReference Property RealWorldOrigin Auto
ImageSpaceModifier Property TeleportIMOD Auto
Sound Property TeleportSound Auto
Message Property CantEnterInCombat Auto
GlobalVariable Property ZP_ProphecyPoints Auto
GlobalVariable Property ZP_ProphecyPointsEarned Auto
Perk[] Property Perks Auto
Message[] Property PerkInfo Auto
Int[] Property ParentA Auto
Int[] Property ParentB Auto
Int[] Property PowerPerk Auto      ; perks whose ability is a power: AddPerk alone does not grant it
Form[] Property PowerSpell Auto     ; a Spell (power) or a Shout (Gap Closer)
Int[] Property GiftPerk Auto        ; perk index -> GiftItem, handed out once per save
Form[] Property GiftItem Auto
Bool[] giftDone
ObjectReference[] Property Stars Auto
ObjectReference[] Property Lines Auto
Int[] Property LineFrom Auto
Int[] Property LineTo Auto
Sound Property UnlockSound Auto
VisualEffect Property AbsorbVFX Auto
EffectShader Property AbsorbFXS Auto
ImageSpaceModifier Property UnlockIMOD Auto
Int Property LevelsPerPoint = 5 Auto
Int Property MaxPoints = 20 Auto

Bool busy
Bool wasThirdPerson

; ---------------------------------------------------------------------------------------- entering / leaving

Function RequestToggle()
	If !busy
		RegisterForSingleUpdate(0.1)
	EndIf
EndFunction

Event OnUpdate()
	busy = True
	If PlayerRef.GetParentCell() == SanctumOrigin.GetParentCell()
		Leave()
	ElseIf PlayerRef.IsInCombat()
		CantEnterInCombat.Show()
	Else
		Enter()
	EndIf
	busy = False
EndEvent

Function Enter()
	AwardPoints()
	RepairPowers()
	GiveGifts(True)
	wasThirdPerson = !PlayerRef.GetAnimationVariableBool("IsFirstPerson")
	RealWorldOrigin.MoveTo(PlayerRef)
	TeleportSound.Play(PlayerRef)
	TeleportIMOD.Apply()
	Utility.Wait(0.7)
	PlayerRef.MoveTo(SanctumOrigin)
	Utility.Wait(1.0)
	RelightAll()
	Debug.Notification("Prophecy points: " + ZP_ProphecyPoints.GetValueInt() + ". Cast Prophecy again to return.")
EndFunction

Function Leave()
	TeleportSound.Play(PlayerRef)
	TeleportIMOD.Apply()
	Utility.Wait(0.7)
	PlayerRef.MoveTo(RealWorldOrigin)
	If wasThirdPerson
		Game.ForceThirdPerson()
	EndIf
	Game.RequestAutoSave()
EndFunction

Function AwardPoints()
	Int due = PlayerRef.GetLevel() / LevelsPerPoint
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

; ---------------------------------------------------------------------------------------- the stars

; Called by ZP_ProphecyNode.OnActivate
Function ActivateNode(Int idx)
	If busy
		Return
	EndIf
	busy = True
	If PerkInfo[idx].Show() == 0
		If PlayerRef.HasPerk(Perks[idx])
			Debug.Notification(Perks[idx].GetName() + " is already learned.")
		ElseIf !Unlocked(idx)
			Debug.Notification("Requires " + RequirementText(idx) + ".")
		ElseIf ZP_ProphecyPoints.GetValueInt() < 1
			Debug.Notification("No Prophecy points. You gain one every " + LevelsPerPoint + " levels.")
		Else
			PlayerRef.AddPerk(Perks[idx])
			GrantPower(idx)
			GiveGifts(True)
			ZP_ProphecyPoints.SetValue(ZP_ProphecyPoints.GetValueInt() - 1)
			Debug.Notification("Learned " + Perks[idx].GetName() + ". Prophecy points: " + ZP_ProphecyPoints.GetValueInt())
			PlayUnlock(idx)
		EndIf
	EndIf
	busy = False
EndFunction

Function PlayUnlock(Int idx)
	ObjectReference star = Stars[idx]
	star.PlayAnimation("PlayAnim02")
	Int j = 0
	While j < Lines.Length
		If (LineFrom[j] == idx || LineTo[j] == idx) && PlayerRef.HasPerk(Perks[LineFrom[j]]) && PlayerRef.HasPerk(Perks[LineTo[j]])
			Lines[j].PlayAnimation("Unlock")
		EndIf
		j += 1
	EndWhile
	UnlockSound.Play(PlayerRef)
	AbsorbVFX.Play(PlayerRef, 8, star)
	UnlockIMOD.Apply()
	Utility.Wait(0.1)
	AbsorbFXS.Play(PlayerRef)
	Utility.Wait(3)
	AbsorbFXS.Stop(PlayerRef)
	Utility.Wait(2)
	AbsorbVFX.Stop(PlayerRef)
EndFunction

Function RelightAll()
	Int i = 0
	While i < Stars.Length
		If PlayerRef.HasPerk(Perks[i])
			Stars[i].PlayAnimation("PlayAnim02")
		EndIf
		i += 1
	EndWhile
	Int j = 0
	While j < Lines.Length
		If PlayerRef.HasPerk(Perks[LineFrom[j]]) && PlayerRef.HasPerk(Perks[LineTo[j]])
			Lines[j].PlayAnimation("Unlocked")
		EndIf
		j += 1
	EndWhile
EndFunction

Bool Function Unlocked(Int idx)
	If ParentA[idx] < 0
		Return True
	EndIf
	If PlayerRef.HasPerk(Perks[ParentA[idx]])
		Return True
	EndIf
	Return ParentB[idx] >= 0 && PlayerRef.HasPerk(Perks[ParentB[idx]])
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
		If PlayerRef.HasPerk(Perks[PowerPerk[k]])
			Give(PowerSpell[k], False)
		EndIf
		k += 1
	EndWhile
EndFunction

; a power is added like any spell; a shout also needs its word taught and unlocked (as Enderal does for its talents)
Function Give(Form f, Bool abVerbose)
	If PlayerRef.HasSpell(f)
		Return
	EndIf
	Shout sh = f as Shout
	If sh
		WordOfPower w = sh.GetNthWordOfPower(0)
		Game.TeachWord(w)
		Game.UnlockWord(w)
		PlayerRef.AddShout(sh)
		If abVerbose
			Debug.Notification("Talent learned: " + sh.GetName())
		EndIf
	Else
		PlayerRef.AddSpell(f as Spell, abVerbose)
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
		If !giftDone[k] && PlayerRef.HasPerk(Perks[GiftPerk[k]])
			giftDone[k] = True
			PlayerRef.AddItem(GiftItem[k], 1, !abVerbose)
		EndIf
		k += 1
	EndWhile
EndFunction
