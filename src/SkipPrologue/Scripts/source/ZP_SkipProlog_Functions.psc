Scriptname ZP_SkipProlog_Functions extends Quest
{Zenderal - Skip The Prologue.

 Runs character creation, rebuilds the state the prologue would have left, then hands off to
 Enderal's own main quest at the point the player wakes up in Jespar's camp - MQ02 "The Void",
 stage 10 - with the Arcane Fever in play.

 The chargen half is Davipb's SkipIntro_Functions shape (proven archetype). The quest half is
 a single SetStage: MQ01's own stage-130 fragment does everything else. See AdvanceMainQuest().}

Import Utility
Import Game

;=====================================================================================
;                                   CHARACTER CREATION
;=====================================================================================

Function BeginSkip()

	; Character creation happens at the camp we are about to wake up in, so the racemenu
	; backdrop is the coast rather than Ark's marketplace. MQ101 still spawns us in Ark -
	; that is what keeps us out of MQP01Home, where the prologue's own start trigger lives -
	; but we leave immediately and never see it.
	PlayerREF.MoveTo(MQ02_D0_PlayersWakeUpmarker02)
	Utility.Wait(1)

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

	; --- the Arcane Fever, as MQP03 and MQ01 would have left it
	; MQP03.StrandingCutscene() adds the fever ability and MQ04's Lishari ritual is what
	; removes it again, so at our start point the player must have it. MQ01.BeginHeadache()
	; then does ModAV("LastFlattered", -15) - Arcane Fever IS that actor value, negated.
	PlayerREF.AddSpell(_00E_MQP03_MagicFeverSpell, False)
	PlayerREF.SetAV("LastFlattered", -15)

	; Re-enable BEFORE the handoff. MQ02 stage 10 disables controls again for its own fade,
	; and stage 15's WakeUpPlayer() re-enables them; doing it the other way round would
	; race with that and could leave the player locked out.
	Game.EnablePlayerControls()

	AdvanceMainQuest()

EndFunction

;=====================================================================================
;                                    QUEST ADVANCE
;=====================================================================================

; This one SetStage is the whole skip. MQ01's stage-130 fragment (_00E_MQ01_Functions.CleanUp)
; resets the timescale, opens the dam gate, unlocks the MQ01 doors, completes MQ01 - so
; "A New Beginning" reads as done in the journal - and then does MQ02.Start() +
; MQ02.SetStage(10).
;
; MQ02 "The Void" stage 10 (MovePlayerAndJesparToStart) teleports the player to
; MQ02_D0_PlayersWakeUpmarker02 and Jespar to MQ02_D0_JesparSpawnMarker, skips to 05:30, and
; chains to stage 15 (WakeUpPlayer) for the fade-in and the woozy get-up idle.
;
; "Arcane Fever" NQ41 needs no handling at all: TIF__000C3FE4, on Jespar's first camp topic
; (MQ02_D0_4b 0C3FD6), calls NQ41.SetStage(5). It arrives as soon as the player talks to him.
;
; The class is likewise chosen in-game - MQ02's later Jespar conversations (topics 146654 and
; 14664F) set MQ02.iPlayerClass and call GivePlayerSkillbook(). Do not pre-set it here; that
; would hand out the starting skillbooks twice.
Function AdvanceMainQuest()

	MQ01.Start()
	MQ01.SetStage(130)

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

Race Property BretonRace Auto
Race Property HighElfRace Auto
Race Property NordRace Auto

GlobalVariable Property TalentPoints Auto
GlobalVariable Property Lernpunkte Auto

MusicType Property _00E_Music_Special_WiegeDesLebens Auto
MusicType Property _00E_Music_Special_Act1Theme Auto

WordOfPower Property _00E_Class_ClassMenuWord Auto
Shout Property _00E_Class_Meditate Auto

ObjectReference Property MQ02_D0_PlayersWakeUpmarker02 Auto

Quest Property MQ01 Auto
