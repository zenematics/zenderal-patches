Scriptname ZP_SkipTTW_Functions extends Quest
{Zenderal - Skip To Taming The Waves.

 Runs character creation, rebuilds the state the prologue would have left, then advances the
 main quest to the end of MQ04 "Taming the Waves".

 The chargen half is Davipb's SkipIntro_Functions shape (proven archetype). The quest half
 walks MQ01 -> MQ04 by SetStage so that ENDERAL'S OWN fragments hand out the rewards and do
 the handoffs - see the note above AdvanceMainQuest(). We deliberately do not duplicate those
 grants here; doing both would double them.}

Import Utility
Import Game

;=====================================================================================
;                                   CHARACTER CREATION
;=====================================================================================

Function BeginSkip()

	Game.PrecacheCharGen()

	PlayerREF.AddItem(ClothesPrisonerRags, 1, True)
	PlayerREF.EquipItem(ClothesPrisonerRags, false, true)

	Debug.SendAnimationEvent(PlayerREF, "IdleForceDefaultState")
	Game.DisablePlayerControls()

	Game.ShowRaceMenu()

	RegisterForSingleUpdate(1)
	_00E_Music_Special_WiegeDesLebens.Add()
	GoToState("Chargen")

EndFunction

State Chargen

	Event OnUpdate()

		If !(Utility.IsInMenuMode())
			GoToState("")
			EndCharacterGeneration()
		Else
			RegisterForSingleUpdate(1)
		EndIf

	EndEvent

EndState

Function EndCharacterGeneration()

	Game.PrecacheCharGenClear()
	_00E_Music_Special_WiegeDesLebens.Remove()

	; --- racial ability, exactly as the prologue assigns it
	If Player.GetRace() == HighElfRace
		PlayerREF.AddSpell(_00E_FS_Ab_RacialAb_Aeterna)
	ElseIf Player.GetRace() == NordRace
		PlayerREF.AddSpell(_00E_FS_Ab_RacialAb_Arazalean)
	ElseIf Player.GetRace() == BretonRace
		PlayerREF.AddSpell(_00E_FS_Ab_RacialAb_Kilean)
	Else
		PlayerREF.AddSpell(_00E_FS_Ab_RacialAb_Qyranian)
	EndIf

	Levelsystem.RemoveAllItemsSafeVersion(None)
	PlayerREF.AddItem(ClothesPrisonerRags, 1, True)
	PlayerREF.EquipItem(ClothesPrisonerRags, false, true)

	TalentPoints.SetValueInt(1)
	Lernpunkte.SetValueInt(1)

	PlayerREF.AddShout(_00E_Class_Meditate)
	PlayerREF.SetAV("dragonsouls", 1)

	Game.UnlockWord(_00E_Class_ClassMenuWord)
	Game.TeachWord(_00E_Class_ClassMenuWord)

	_00E_Music_Special_Act1Theme.Add()

	; NOTE: we never add _00E_MQP03_MagicFeverSpell ("Weird Fever"). SkipIntro does, because it
	; stops at MQ01 and the fever is still in play there. MQ04 is where Lishari's ritual removes
	; it, so at our start point the player must not have it. ClearArcaneFeverState() below also
	; removes it defensively in case something else applied it.

	ChooseClass()
	AdvanceMainQuest()
	ClearArcaneFeverState()

	Game.EnablePlayerControls()

EndFunction

;=====================================================================================
;                                     CLASS CHOICE
;=====================================================================================

; MQ02.iPlayerClass is normally written only by the dream-sequence dialogue fragments
; (tif__0014665b/c/d, tif__0014665f/60/61/62). Skipping MQ02 means nothing sets it, and
; GivePlayerSkillbook() would then hand out nothing at all - so we ask and set it ourselves.
; Enderal's values: 1 = rogue, 2 = mage, 3 = warrior.
Function ChooseClass()

	Int iChoice = ZP_SkipTTW_sClassChoice.Show()

	If iChoice == 0
		MQ02.iPlayerClass = 3       ; Warrior
	ElseIf iChoice == 1
		MQ02.iPlayerClass = 2       ; Mage
	Else
		MQ02.iPlayerClass = 1       ; Rogue
	EndIf

	MQ02.GivePlayerSkillbook()

EndFunction

;=====================================================================================
;                                    QUEST ADVANCE
;=====================================================================================

; Walk the chain by its own completing stages, in order, so Enderal's fragments run:
;   MQ01 130 -> MQ02 170 -> MQ03 48 -> MQ04 95
; Each quest's completing fragment also starts the next (MQ01 -> MQ02.Start()/SetStage(10),
; MQ02 -> MQ03.SetStage(5), MQ03 -> MQ04.Start()/SetStage(10) + CQJ01.SetStage(5)), and hands
; out that quest's EP/gold/scrolls. Start() before each SetStage is belt-and-braces in case a
; handoff did not land.
;
; Stage indices verified against reference/base/Skyrim/Quests/ - each is the stage flagged
; CompleteQuest. MQ02 has a second completing stage (175) for the other branch; 170 is the one
; whose fragment performs the handoff.
Function AdvanceMainQuest()

	MQ01.Start()
	MQ01.SetStage(130)
	Utility.Wait(1)

	MQ02.Start()
	MQ02.SetStage(170)
	Utility.Wait(1)

	MQ03.Start()
	MQ03.SetStage(48)
	Utility.Wait(1)

	MQ04.Start()
	MQ04.SetStage(95)
	Utility.Wait(1)

EndFunction

; Idempotent. MQ04's own FinishUp()/RitualFailsave() do these two removals; repeating them is
; harmless and covers the case where a fragment did not run.
Function ClearArcaneFeverState()

	PlayerREF.RemoveSpell(_00E_MQP03_MagicFeverSpell)
	PlayerREF.RemoveSpell(_00E_MQ04_FeuerloescherSpell)

EndFunction

;=====================================================================================
;                                     PROPERTIES
;=====================================================================================

_00E_QuestFunctions Property Levelsystem Auto

Armor Property ClothesPrisonerRags Auto

ActorBase Property Player Auto
Actor Property PlayerREF Auto

Spell Property _00E_FS_Ab_RacialAb_Aeterna Auto
Spell Property _00E_FS_Ab_RacialAb_Arazalean Auto
Spell Property _00E_FS_Ab_RacialAb_Kilean Auto
Spell Property _00E_FS_Ab_RacialAb_Qyranian Auto
Spell Property _00E_MQP03_MagicFeverSpell Auto
Spell Property _00E_MQ04_FeuerloescherSpell Auto

Race Property RedguardRace Auto
Race Property BretonRace Auto
Race Property HighElfRace Auto
Race Property NordRace Auto

GlobalVariable Property TalentPoints Auto
GlobalVariable Property Lernpunkte Auto

MusicType Property _00E_Music_Special_WiegeDesLebens Auto
MusicType Property _00E_Music_Special_Act1Theme Auto

WordOfPower Property _00E_Class_ClassMenuWord Auto
Shout Property _00E_Class_Meditate Auto

Message Property ZP_SkipTTW_sClassChoice Auto

Quest Property MQ01 Auto
_00E_MQ02_Functions Property MQ02 Auto
Quest Property MQ03 Auto
Quest Property MQ04 Auto
