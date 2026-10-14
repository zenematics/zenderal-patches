Scriptname _00E_EPUpdateFunctions extends Actor


import Math
int MapMarkersDiscoveredCounter = 0
int LocksPickedCounter = 0
int ItemsPickpocketedCounter = 0
int ItemsStolenCounter = 0
int PotionsMixedCounter = 0
int PoisonsMixedCounter = 0
int ArmorMadeCounter = 0
int WeaponsMadeCounter = 0
int SoulsTrappedCounter = 0
int MagicItemsMadeCounter = 0
int IntimidationsCounter = 0
int QuestsCompletedCounter = 0

;=====================================================================================
;              							EVENTS                  					 
;=====================================================================================

Event OnInit()
	if Self == Player
		GoToState("RealPlayer")
		(Player as _00E_PlayerFunctions).InitCombatMusic()
		RegisterForSingleUpdate(2.0)
	Endif
EndEvent

Event OnPlayerLoadGame()
	If self == Player ; A check just in case. Most likely this condition is always True	
		If GetState() != "RealPlayer" ; Post-1.2.5.0 version update
			GoToState("RealPlayer")
		EndIf
		UpdateLevelUpSystem() ; Failsafe and version update
		(Player as _00E_PlayerFunctions).InitCombatMusic() ; Version update from 1.5.2.0 or earlier
		UnregisterForUpdate()
		RegisterForSingleUpdate(3.5)
	EndIf
EndEvent

State RealPlayer

	Event OnUpdate()
		Int delta

		delta = Game.QueryStat("Locations Discovered") - MapMarkersDiscoveredCounter
		If delta > 0
			MapMarkersDiscoveredCounter += delta
			_00E_Player_sEPGained_Discovery.Show()
			receiveEP(40 * delta)

			If MapMarkersDiscoveredCounter >= 50 && !bMapMarkersAchievementUnlocked && _00E_AchievementsEnabled.GetValueInt() == 1
				bMapMarkersAchievementUnlocked = True
				Steam.UnlockAchievement("END_LOCATIONS_01")
			EndIf
		EndIf

		delta = Game.QueryStat("Locks Picked") - LocksPickedCounter
		If delta > 0
			LocksPickedCounter += delta
			_00E_Player_sEPGained_LockPicked.Show()
			receiveEP(15 * delta)
		EndIf
		
		delta = Game.QueryStat("Potions Mixed") - PotionsMixedCounter
		If delta > 0
			PotionsMixedCounter += delta
			_00E_Player_sEPGained_PotionMixed.Show()
			receiveEP(3 * delta)
		EndIf
		
		delta = Game.QueryStat("Poisons Mixed") - PoisonsMixedCounter
		If delta > 0
			PoisonsMixedCounter += delta
			_00E_Player_sEPGained_PoisonMixed.Show()
			receiveEP(3 * delta)
		EndIf
		
		delta = Game.QueryStat("Armor Made") - ArmorMadeCounter
		If delta > 0
			ArmorMadeCounter += delta
			_00E_Player_sEPGained_ArmorMade.Show()
			receiveEP(20 * delta)
		EndIf
		
		delta = Game.QueryStat("Weapons Made") - WeaponsMadeCounter
		If delta > 0
			WeaponsMadeCounter += delta
			_00E_Player_sEPGained_WeaponsMade.Show()
			receiveEP(20 * delta)
		EndIf

		delta = Game.QueryStat("Souls Trapped") + SoulsCaught.GetValueInt() - SoulsTrappedCounter
		If delta > 0
			SoulsTrappedCounter += delta
			_00E_Player_sEPGained_SoulCaptured.Show()
			receiveEP(10 * delta)
		EndIf
		
		delta = Game.QueryStat("Magic Items Made") - MagicItemsMadeCounter
		if delta > 0
			MagicItemsMadeCounter += delta
			_00E_Player_sEPGained_MagicItemMade.Show()
			receiveEP(30 * delta)
		EndIf
		
		delta = Game.QueryStat("Intimidations") - IntimidationsCounter
		If delta > 0
			IntimidationsCounter += delta
			_00E_Player_sEPGained_Intimidations.Show()
			receiveEP(50 * delta)
		EndIf

		if ShowEXPMessage == False && PlayerEXP.GetValue() >= 120 && (_00E_DisableQuestTutorials.GetValueInt() == 0)
			ShowEXPMessage = true
			Message.ResetHelpMessage("Empty")
			_00E_Tutorial_EPSystem.ShowAsHelpMessage("Empty", 4.0, 3.0, 1)
		EndIf
		
		If _00E_OreVeinsMined.GetValueInt() >= 50 && !bOreAchievementUnlocked && _00E_AchievementsEnabled.GetValueInt() == 1
			bOreAchievementUnlocked = true
			Steam.UnlockAchievement("END_ORE_01")
		EndIf
		
		delta = Game.QueryStat("Quests Completed") - QuestsCompletedCounter
		if delta > 0
			QuestsCompletedCounter += delta
			If QuestsCompletedCounter >= 50 && !bDoneQuestCompleted && _00E_AchievementsEnabled.GetValueInt() == 1
				bDoneQuestCompleted = true
				Steam.UnlockAchievement("END_QUESTS_01")
			EndIf
		EndIf
		
		If _00E_RhetorikCounter.GetValueInt() >= 15 && !bRhetoricAchievementUnlocked && _00E_AchievementsEnabled.GetValueInt() == 1
			bRhetoricAchievementUnlocked = true
			Steam.UnlockAchievement("END_RHETORIC_01")
		EndIf

		; Arcane fever management
		Int iArcaneFever = -1*(Player.GetAV("LastFlattered")) as Int

		; ZP: isdead latches True on a fever death and nothing ever clears it. If Kill() did not
		; ZP: actually kill the player, the flag is saved and blocks every level-up and the fever
		; ZP: 40/70 effects forever. Release it once the player is alive and below 100 fever.
		If isdead && !Player.IsDead() && iArcaneFever < 100
			isdead = False
		EndIf

		If iArcaneFever >= 100 && isdead == False
			isdead = True
			Player.Kill()
			_00E_Player_sArcaneFever_Death.Show()
			If _00E_AchievementsEnabled.GetValueInt() == 1 && !bDoneArcanistsFever
				bDoneArcanistsFever = true
				Steam.UnlockAchievement("END_ARCANISTS_FEVER_01")
			EndIf
		EndIf

		If isdead == False
			If iArcaneFever >= 90 
				iArcaneFeverWarnCounter -= 1
				If iArcaneFeverWarnCounter <= 0
					iArcaneFeverWarnCounter = 20
					Message.ResetHelpMessage("Empty")
					_00E_Player_sArcaneFever_Critical.ShowAsHelpMessage("Empty", 5, 1, 1)
				EndIf
			Else ; iArcaneFever < 90
				iArcaneFeverWarnCounter = 0 ; Reset
			EndIf

			If iArcaneFever >= 40
				If Player.HasSpell(_00E_Arkanistenfieber40) == False
					Player.AddSpell(_00E_Arkanistenfieber40,0)
					Message.ResetHelpMessage("Empty")
					_00E_Player_sArcaneFever_Worsen.ShowAsHelpMessage("Empty", 3, 1, 1)
				EndIf
			Else ; iArcaneFever < 40
				If Player.HasSpell(_00E_Arkanistenfieber40)
					Player.RemoveSpell(_00E_Arkanistenfieber40)
					_00E_Player_sArcaneFever_Cure.Show()
				EndIf
			EndIf

			If iArcaneFever >= 70
				If Player.HasSpell(_00E_Arkanistenfieber70) == False
					Player.AddSpell(_00E_Arkanistenfieber70,0)
					Message.ResetHelpMessage("Empty")
					_00E_Player_sArcaneFever_Worsen.ShowAsHelpMessage("Empty", 4, 1, 1)
				EndIf
			Else ; iArcaneFever < 70
				If Player.HasSpell(_00E_Arkanistenfieber70)
					Player.RemoveSpell(_00E_Arkanistenfieber70)
					_00E_Player_sArcaneFever_Cure.Show()
				EndIf
			EndIf
		EndIf

		; Level up
		If iLevelUpsNeeded > 0
			; Level up if not in combat, not in dialogue, activate controls enabled (not in a scene?) and, obviously, not dead
			While !IsInCombat() && UI.IsMenuOpen("Dialogue Menu") == False && Game.IsActivateControlsEnabled() && !Player.IsDead() && (isdead == False) && (iLevelUpsNeeded > 0)
				levelUp()
			EndWhile
		EndIf
		
		If bShowHeroMenuHelpBox && (_00E_DisableMenuTutorials.GetValueInt() == 0)
			bShowHeroMenuHelpBox = False
			Message.ResetHelpMessage("Empty")
			_00E_Tutorial_HeroMenue.ShowAsHelpMessage("Empty", 7, 30, 1)
		EndIf

		RegisterForSingleUpdate(3.5) ; seems like a decent value
	EndEvent


	Event OnDeath(Actor akKiller)

		if Player.IsInCombat()
			_00E_Player_sIdiot.Show()
			receiveEP(1000)
		EndIf
		
	EndEvent

EndState

Event OnDeath(Actor akKiller)
	; Papyrus compiler demands this event to be defined in the empty state
EndEvent


;=====================================================================================
;              						LEVELSYSTEM FUNCTIONS                   					 
;=====================================================================================

Int iLevelUpsNeeded = 0
Bool _bLevelUpSystemLocked = False

Function _LockLevelUpSystem()
	While _bLevelUpSystemLocked
		Utility.WaitMenuMode(0.1)
	EndWhile
	_bLevelUpSystemLocked = True
EndFunction

Function _UnlockLevelUpSystem()
	_bLevelUpSystemLocked = False
EndFunction

Function UpdateLevelUpSystem()
	_LockLevelUpSystem()
	iLevelUpsNeeded = getLevelUpCount()
	_UnlockLevelUpSystem()
EndFunction


function levelUp()
{Opens a menu allowing the player to choose which attribute he/she wants to increase; sets all attributes (talentPoints, Lernpunkte, Handwerkspunkte,...)}

	_LockLevelUpSystem()
	PlayerLevel.Mod(1)
	iLevelUpsNeeded = getLevelUpCount()
	_UnlockLevelUpSystem()
	
	if UILevelUp
		UILevelUp.Play(Player)
	elseif _00E_Track_Success
		_00E_Track_Success.Add()
	Endif

	Utility.Wait(1) ;added a Wait() between the audio cue and the level up prompt to give the player an early warning about the incoming message box
	
	int iMessage = _00E_Levelup.show(PlayerLevel.GetValueInt(),Player.GetBaseAV("Health"), Player.GetBaseAV("Magicka"), Player.GetBaseAV("Stamina"))
	Game.SetPlayerLevel(PlayerLevel.GetValueInt())
	TalentPoints.Mod(1)
	Player.SetAV("dragonsouls", TalentPoints.GetValueInt())
	Lernpunkte.Mod(5)
	Handwerkspunkte.Mod(4)
			
	if iMessage == 0 
		Player.SetActorValue("Health", Player.GetBaseAV("Health")+9)
	elseif iMessage == 1 
		Player.SetActorValue("Magicka", Player.GetBaseAV("Magicka")+8)
	elseif iMessage == 2 
		Player.SetActorValue("Stamina", Player.GetBaseAV("Stamina")+11)
	endif

	Int iPlayerLevel = PlayerLevel.GetValueInt()
	If iPlayerLevel >= 2 && iPlayerLevel <= 5
		bShowHeroMenuHelpBox = True
	EndIf

Endfunction

bool function receiveEP(int amount)
{Adds the given amount of EP to the player and displays it as notification}
	
	_LockLevelUpSystem()
	PlayerExp.Mod(amount)
	Int iLevelUpCount = getLevelUpCount()
	iLevelUpsNeeded = iLevelUpCount 
	_UnlockLevelUpSystem()

	PlayerNeededExp.SetValue(ComputeNeededExp((PlayerLevel.GetValueInt()+iLevelUpCount), EXPMultSlope.GetValue(), EXPMult.GetValue()))
	
	int iNeededExpNextLevel = (PlayerNeededExp.GetValueInt()-PlayerExp.GetValueInt())
	_00E_sEPNeeded.Show(amount, iNeededExpNextLevel)

	return true
	
Endfunction

int function getLevelUpCount()
{Calculates how many level ups the player should receive based on his current ep count, changes none of the global variables}
	int iCurrentExp = PlayerExp.GetValueInt()
	int iCurrentLevel = PlayerLevel.GetValueInt()
	bool LevelCheckRequired = true
	int iLevelUpsAchieved = 0
	float NeededExp

	While LevelCheckRequired
		LevelCheckRequired = false
		NeededExp = ComputeNeededExp(iCurrentLevel, EXPMultSlope.GetValue(), EXPMult.GetValue())
	
		if iCurrentExp >= NeededExp
			LevelCheckRequired = true
			iLevelUpsAchieved += 1
			iCurrentLevel += 1
		endif
		
	Endwhile
    
	return iLevelUpsAchieved

EndFunction

float Function ComputeNeededExp(int CurrentLevel, float Slope, float Mult)
{Computes the total Experience (EP) needed by the player to reach the level CurrentLevel + 1. This includes the experience needed for the previous level.}
	
	; commented out as it is useless upon the Steam releases
	; GlobalVariable _00E_FS_IsForgottenStoriesActivated = Game.GetForm(0x0004320E) as GlobalVariable
	; If _00E_FS_IsForgottenStoriesActivated.GetValueInt() == 0
        ; Pre-DLC formula:
        ; return pow(CurrentLevel, Slope) * Mult
    ; EndIf

    ; This can be used as a quick way to scale the leveling process
    ; for all levels:
	float fExpAcc = 1.0
	float fExpAcc_Level20 = 1.2
	float fExpAcc_Level30 = 1.5
	float fExpAcc_Level40 = 2.0

    Mult *= fExpAcc

    If CurrentLevel <= 20
        ; no changes to the old formula until level 20.
        return pow(CurrentLevel, Slope) * Mult
    Else
        ; no changes to the old formula for the first 20 levels.
        float result = pow(20, Slope) * Mult
        ; Progressive taxation:
        if CurrentLevel <= 30
            result += (pow(CurrentLevel, Slope) - pow(20, Slope)) * Mult * fExpAcc_Level20
            return result
        elseif CurrentLevel <= 40
            result += (pow(30, Slope) - pow(20, Slope)) * Mult * fExpAcc_Level20
            result += (pow(CurrentLevel, Slope) - pow(30, Slope)) * Mult * fExpAcc_Level30
            return result
        else
            result += (pow(30, Slope) - pow(20, Slope)) * Mult * fExpAcc_Level20
            result += (pow(40, Slope) - pow(30, Slope)) * Mult * fExpAcc_Level30
            result += (pow(CurrentLevel, Slope) - pow(40, Slope)) * Mult * fExpAcc_Level40
            return result
        endif
    EndIf

EndFunction

; A debugging function:
;function DumpLevelCurve()
;{Dump a table of required EP for each level from 0 to 100 to the Papyrus log}
;	string aua = ""
;	int iIndex = 0
;	while iIndex < 100
;		aua += "To get to level " + (iIndex + 1) + ", you need " + ComputeNeededExp(iIndex, EXPMultSlope.GetValue(), EXPMult.GetValue()) + "EP. \n "
;		iIndex += 1
;	endwhile
;	Debug.Trace(aua)
;Endfunction

;=====================================================================================
;              							PROPERTIES                  					 
;=====================================================================================

Message Property _00E_Player_sEPGained_WeaponsMade Auto
Message Property _00E_Player_sEPGained_SoulCaptured Auto
Message Property _00E_Player_sEPGained_PotionMixed Auto
Message Property _00E_Player_sEPGained_PoisonMixed Auto
Message Property _00E_Player_sEPGained_MagicItemMade Auto
Message Property _00E_Player_sEPGained_ArmorMade Auto
Message Property _00E_Player_sEPGained_LockPicked Auto
Message Property _00E_Player_sEPGained_Intimidations Auto
Message Property _00E_Player_sEPGained_Discovery Auto
Message Property _00E_Player_sArcaneFever_Worsen Auto
Message Property _00E_Player_sArcaneFever_Death Auto
Message Property _00E_Player_sArcaneFever_Critical Auto
Message Property _00E_Player_sArcaneFever_Cure Auto
Message Property _00E_Player_sIdiot Auto
Message Property _00E_sEPNeeded Auto
Message Property _00E_Levelup Auto
Message Property _00E_Tutorial_EPSystem Auto
Message Property _00E_Tutorial_HeroMenue Auto

Actor Property Player Auto
Spell Property _00E_Arkanistenfieber40 Auto
Spell Property _00E_Arkanistenfieber70 Auto
GlobalVariable Property PlayerExp auto
GlobalVariable Property PlayerLevel auto
GlobalVariable Property PlayerNeededExp auto
GlobalVariable Property Handwerkspunkte auto
GlobalVariable Property Lernpunkte auto
GlobalVariable Property EXPMult auto
GlobalVariable Property EXPMultSlope auto
GlobalVariable Property SoulsCaught Auto
GlobalVariable Property _00E_DisableMenuTutorials Auto
GlobalVariable Property _00E_DisableQuestTutorials Auto
GlobalVariable Property _00E_AchievementsEnabled Auto
GlobalVariable Property _00E_OreVeinsMined Auto
GlobalVariable Property _00E_RhetorikCounter Auto
GlobalVariable Property TalentPoints Auto
MusicType Property _00E_Track_Success Auto
Sound Property UILevelUp Auto

bool isdead
Bool ShowEXPMessage
bool bShowHeroMenuHelpBox = false
bool bDoneQuestCompleted = false
bool bDoneArcanistsFever = false
bool bOreAchievementUnlocked = false
bool bRhetoricAchievementUnlocked = false
bool bMapMarkersAchievementUnlocked = false
Int iArcaneFeverWarnCounter = 0