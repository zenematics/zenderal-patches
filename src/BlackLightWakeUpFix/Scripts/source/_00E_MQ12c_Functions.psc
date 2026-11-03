Scriptname _00E_MQ12c_Functions extends Quest Conditional

Import Utility

; This script is mainly used for handling the different "debris" stages of Ark after the siege

int function _GetScriptVersion() Global
    return 1
endFunction

;=====================================================================================
;                                        EVENTS                                      
;=====================================================================================

Event OnUpdate()

    If iWakeUpWatchdog > 0 ; ZP
        WakeUpWatchdog()
    ElseIf MQ12c_SC03_Dream.IsPlaying()
        If GameHour.GetValue() >= 20
            Timescale.SetValue(0.01)
        Else
            RegisterForSingleUpdate(1)
        EndIf
    Else
        UnregisterForUpdate()
    EndIf

EndEvent

Event OnUpdateGameTime()

    DebrisLevel02()
    DeleteSC01Stuff()
    
EndEvent

;=====================================================================================
;                                        FUNCTIONS                                       
;=====================================================================================

Function DebrisLevel01()

    ; Ark directly after the Nehrimese's attack, corpses are still around, sigils are enabled

    int iIndex = _00E_MQ12c_HarborNPCs.GetSize()
    
    while iIndex > 0
        iIndex -= 1
        ObjectReference objToDisable = _00E_MQ12c_HarborNPCs.GetAt(iIndex) as ObjectReference
        objToDisable.Disable()
    endwhile
    
    iIndex = _00E_MQ12c_SoldierNPCs.GetSize()
    
    while iIndex > 0
        iIndex -= 1
        ObjectReference objToEnable = _00E_MQ12c_SoldierNPCs.GetAt(iIndex) as ObjectReference
        objToEnable.Enable()
        ; Failsave to prevent a bug in which some of the Possessed
        ; enabled at this point would be in ghostmode and therefore
        ; invincible
        ; ( http://sureai.net:9898/browse/ERB-846 ).
		; EDIT Till 03/Nov/2018: This doesn't really fix the issue, but I leave the code in here just in case
		; see comment below
        Actor objAsActor = (objToEnable as Actor)
        if objAsActor != None
            if (objToEnable as _00E_EPOnDeath)
                ; Checking (by typecast) that objAsActor is an enemy.
                objAsActor.SetGhost(False)
            endif
        endif
    endwhile
    
    iIndex = _00E_MQ12c_FireNPCs.GetSize()
    
    while iIndex > 0
        iIndex -= 1
        ObjectReference objToEnable = _00E_MQ12c_FireNPCs.GetAt(iIndex) as ObjectReference
        objToEnable.Enable()
        ; Failsave to prevent a bug in which some of the Possessed
        ; enabled at this point would be in ghostmode and therefore
        ; invincible
        ; ( http://forum.sureai.net//tracker.php?p=8&t=10425 ).
		; EDIT Till 03/Nov/2018: This doesn't really fix the issue, but I leave the code in here just in case
		; see comment below
        Actor objAsActor = (objToEnable as Actor)
        if objAsActor != None
            objAsActor.SetGhost(False)
        endif
    endwhile

	; Till 03/Nov/2018: The possessed NPCs need to be enabled in a separate formlist (could have been also done via EnableParent)
	; Anyway, the reason behind this is fairly simple: The script _00E_MQ12c_HarbirSiegeSC uses also the formlists 
	; _00E_MQ12c_FireNPCs and _00E_MQ12c_SoldierNPCs but the script actually sets the ghost flag to 1 upon leaving the respective trigger
	; and hence the flag can't be set for an actor's reference it gets set for the actor base
	; resulting in all actor references of the possessed NPCs that are included in the formlist being flagged as ghost
	; I took the possessed NPCs out of those lists and created this new one, that isn't used by the harbor trigger at all
	_00E_Func_ReferenceFormList.Enable(_00E_MQ12c_PossessedNPCs)

    MQ12c_SC1_ExecutionDoor001.BlockActivation(True)
    MQ12c_SC1_ExecutionDoor001.SetLockLevel(255)
    MQ12c_SC1_ExecutionDoor001.SetOpen(False)
    MQ12c_SC1_ExecutionDoor001.Lock(True)
    MQ12c_WestGate_BarrierREF.Enable()
	MQ12c_NorthGate_BarrierREF.Enable()
	MQ12c_MyradOutsideGate_BarrierREF.Enable()
	MQ12c_SouthGate_BarrierREF.Enable()
    MQ12c_SC01_FailsaveREF.Enable()
    MQ12c_HarborGate_BarrierREF.Enable()
    MQ12b_SC6_ArcherMarker.Disable()
    MQ12b_SC6_HarborLinker.Disable()
    MQ12c_GuardLinker.Disable()
    _00E_MC_TaranorREF.Disable()
    _00E_SC_AlmaREF.Disable()
    MQ12c_DisableBoat.Disable()
    MQ12c_Debris_NPC_Linker.Enable()
    MQ12c_NehrimeseScoutREF.Enable()
    MQ12c_Debris_Smoke_Linker.Enable()
    MQ12c_Debris_Level_01_Linker.Enable()
    MQ12cDebrisLight.MoveTo(NightLightsMarker, abMatchRotation = False) ; Hide one lantern light in Ark's Stranger Quarter
    RegisterForSingleUpdateGameTime(72) ; Wait three days to proceed to next debris stage
    
EndFunction

Function DebrisLevel02()

    MQ12b_SC14_SiegeTempleMarker.Disable()
    MQ12c_Debris_Level_01_Linker.Disable()
    ; Corpses have been carried removed, first repairs have started 
    MQ12c_Debris_Level_02_Linker.Enable()
    MQ12cDebrisLight.MoveToMyEditorLocation() ; Unhide lantern light in Ark's Stranger Quarter
    MQ12cDebrisLight = None ; No need to keep it persistent anymore
    
EndFunction

Function SetUpSC01()
    
    MQ12c_SC2_Bed.SetActorOwner(PlayerREF.GetActorBase())
    MQ12c_SC2_Bed.BlockActivation(True)
    _00E_MC_TealorRef.Disable()
    _00E_MC_NataraRef.Disable()
    MQ12c_SC1_ExecutionVoiceTealor001.Enable()
    MQ12c_SC1_ExecutionDoor001.SetLockLevel(255)
    MQ12c_SC1_ExecutionDoor001.SetOpen(False)
    MQ12c_SC1_ExecutionDoor001.Lock(True)

EndFunction

Function CleanUpSC01()

    _00E_MC_TealorRef.Enable()
    _00E_MC_NataraRef.Enable()
    
EndFunction

Function DeleteSC01Stuff()

    MQ12c_SC1_ExecutionVoiceTealor001.Disable()
    MQ12c_SC1_ExecutionDoor001.SetLockLevel(0)
    MQ12c_SC1_ExecutionDoor001.SetOpen(False)
    MQ12c_SC1_ExecutionDoor001.Lock(False)
    
EndFunction

Function ShowMessageBoxBeforeSleeping()

    If ((CQJ04.IsRunning()) && (CQC04.IsRunning()))
        If !CQJ04.IsCompleted() && !CQC04.IsCompleted()
            int iButton01 = _00E_MQ12c_SleepJesparCaliaMsg.Show()
                If iButton01 == 0 
                    SetCurrentStageID(15)
                Else 
                    Return
                EndIf
        ElseIf CQJ04.IsCompleted() && !CQC04.IsCompleted()
                int iButton02 = _00E_MQ12c_SleepCaliaMsg.Show()
                If iButton02 == 0 
                    SetCurrentStageID(15)
                Else 
                    Return
                EndIf
        ElseIf !CQJ04.IsCompleted() && CQC04.IsCompleted()
                int iButton03 = _00E_MQ12c_SleepJesparMsg.Show()
                If iButton03 == 0 
                    SetCurrentStageID(15)
                Else 
                    Return
                EndIf
        Elseif CQJ04.IsCompleted() && CQC04.IsCompleted()
            SetCurrentStageID(15)
        EndIf
    ElseIf (CQJ04.IsRunning()) && !(CQJ04.IsCompleted())
            int iButton04 = _00E_MQ12c_SleepJesparMsg.Show()
                If iButton04 == 0 
                    SetCurrentStageID(15)
                Else 
                    Return
                EndIf
    ElseIf (CQC04.IsRunning()) && !(CQC04.IsCompleted())    
            int iButton05 = _00E_MQ12c_SleepCaliaMsg.Show()
            If iButton05 == 0 
                SetCurrentStageID(15)
            Else 
                Return
            EndIf
    Else
        SetCurrentStageID(15)
    EndIf
    
EndFunction

Function StartSC02()

    _00E_SilenceTransitionLowPriority.Add()

    If (!CQC04.IsCompleted()) && CQC04.IsRunning()
        CQC04.SetCurrentStageID(20)
    EndIf
    
    If (!CQJ04.IsCompleted()) && CQJ04.IsRunning()
        CQJ04.SetCurrentStageID(40)
    EndIf

    _00E_Func_AIWalk.PlayerAIWalk()
    Game.ForceThirdPerson()
    MQ12c_SC02_DreamGoToSleep.ForceStart()

EndFunction

Function FadeToBlack()
    
    SetObjectiveCompleted(10)
    SetCurrentStageID(20)

EndFunction

Function StartSC03()
    
    fTimescaleBefore = TimeScale.GetValue()
    
    MQ10a_SC1_HeartParentREF.Enable()
    MQ12c_SC03_FatherREF.Enable()
    MQ12c_SC03_FatherREF.MoveTo(MQ12c_SC3_FatherMarkerREF)
    MQ12c_SC03_FatherREF.SetOutfit(_00E_Father_Outfit_VeryDecayed)
    
    If MQP01_FatherRef.IsEnabled()
        MQP01_FatherRef.Disable()
    EndIf
    
	_FS_Phasmalist_ControlQuest.UnsummonApparitionIfExists()
    FadeToBlackIMOD.Apply()
    Wait(1)
    _00E_TimeControl.SkipTimeToHour(18.5)
    FadeToBlackHoldImod.ApplyCrossFade(1)
    PlayerREF.MoveTo(PlayerStartMarkerNew)
    _00E_SilenceTransitionLowPriority.Remove()
    _00E_PlayerFunctions.GetSoundControl().RemoveSilence()
    _00E_Func_AIWalk.PlayerAIWalkStop()
    Game.ShowFirstPersonGeometry(False)
    Game.RequestAutoSave()
	fPlayerScale = _00E_SetActorScale.Change(PlayerREF, 0.85)
    TimeScale.SetValue(0.1)
    ImageSpaceModifier.RemoveCrossFade(3)
    Game.ForceFirstPerson()
    Game.DisablePlayerControls(false, true, true, false, true, false, false)
    Wait(3.0)
    Game.EnablePlayerControls()
    Game.DisablePlayerControls(false, true, true, false, true, true, true, true, 0)

    MQ12c_SC03_Dream.ForceStart()
    
    Wait(2)
    
    SetObjectiveDisplayed(15)
    
EndFunction

Function SetTimescale()

    TimeScale.SetValue(450)
    RegisterForSingleUpdate(1)

EndFunction

Function OpenForbiddenDoor()

    MQ12c_SC03_ForbiddenDoorREF.SetOpen(True)

EndFunction

Function EndSC03()

    PlayerREF.SetScale(fPlayerScale)
    _00E_MQ10a_DreamCollapseIMOD.Apply()
    Wait(4)
    FadeToBlackHoldImod.ApplyCrossFade(1)
    MQ12c_SC03_FatherREF.Disable()
    _00E_Music_Special_Dreams.Remove()
    SetObjectiveCompleted(10)
    SetObjectiveCompleted(15)
    SetCurrentStageID(40)
    
EndFunction

Function StartSC04()

    _00E_MC_JesparREF.SetOutfit(_00E_MC_JesparOutfit)
    _00E_Music_Special_Dreams.Remove()
    _00E_SilenceTransitionLowPriority.Add()
    _00E_Func_AIWalk.PlayerAIWalkStop()
    Game.ForceThirdPerson()
    MQ12c_SC04_DoorREF.SetOpen(true)
    PlayerREF.MoveTo(MQ12c_SC04_CompanionRunREF)
    SetCompanion() 
    
    If Companion.IsDisabled()
        Companion.Enable()
    EndIf
    
    Companion.MoveTo(MQ12c_SC04_CompanionMarkerREF)
    TimeScale.SetValue(fTimescaleBefore)
    MQ12c_SC04_WakeUp.ForceStart()
    Game.SetHudCartMode(false)
    ; ZP: the scene's first phase only ends (and FadeBack only runs) once the player lies in
    ; MQ12c_SC2_Bed; if the player never gets there the screen stays black for good
    bFadedBack = False
    iWakeUpWatchdog = 1
    RegisterForSingleUpdate(15)

EndFunction

; ZP: wake-up watchdog, see StartSC04
Function WakeUpWatchdog()

    If bFadedBack || !MQ12c_SC04_WakeUp.IsPlaying()
        iWakeUpWatchdog = 0
    ElseIf iWakeUpWatchdog == 1
        ; Step 1: the player is not in (or getting into) the bed, so put them in it through the
        ; bed's own script, which lies them down without the sleep menu at this stage
        iWakeUpWatchdog = 2
        If PlayerREF.GetSitState() == 0
            MQ12c_SC2_Bed.Activate(PlayerREF)
        EndIf
        RegisterForSingleUpdate(15)
    Else
        ; Step 2: still no fade-in, so give the screen and the controls back and let the player
        ; lie down themselves; that completes the phase and the scene carries on
        iWakeUpWatchdog = 0
        MQ12c_SC2_Bed.BlockActivation(False)
        FadeBack()
        Game.EnablePlayerControls()
        Game.SetHudCartMode(False)
    EndIf

EndFunction

Function FadeBack()

    bool bAlreadyFaded = bFadedBack ; ZP: the watchdog's step 2 faded in already
    bFadedBack = True ; ZP
    Game.SetPlayerAIDriven(False)
    _00E_Func_AIWalk.PlayerAIWalkStop()
    If !bAlreadyFaded ; ZP
        FadeToBlackBackLongImod.ApplyCrossFade(afFadeDuration = 1.0)
    EndIf

EndFunction

Function SetCompanion() 

    If SympathyCalia.GetValueInt() > SympathyJespar.GetValue()
        Companion = _00E_MC_CaliaREF
    Else
        Companion = _00E_MC_JesparREF
    EndIf
    
    SC04_Companion.ForceRefTo(Companion)
    
    If (Companion == _00E_MC_CaliaREF) && (SympathyJespar.GetValueInt() >= __Config_RomanceThreshold)
        bAskForLoveInterest = True
    Elseif (Companion == _00E_MC_JesparREF) && (SympathyCalia.GetValueInt() >= __Config_RomanceThreshold)
        bAskForLoveInterest = True
    Else
        bAskForLoveInterest = False
    EndIf
    
EndFunction

Function ActivateBed()
 
    _00E_Func_RefreshFace.RefreshFace() 
    MQ12c_SC2_Bed.Activate(PlayerREF, True)
    Game.EnablePlayerControls()
    Game.SetPlayerAIDriven(False)
    Game.SetHudCartMode(False)

EndFunction

Function CleanUpAndStartMQ13()

    Game.EnablePlayerControls()
    Game.SetHudCartMode(false)
    _00E_SilenceTransitionLowPriority.Remove()
    _00E_PlayerFunctions.GetSoundControl().RemoveSilence()
	MQ12c_SC01_FailsaveREF.Disable()
    MQ12c_SC1_ExecutionDoor001.Lock(False)
    MQ12c_SC1_ExecutionDoor001.BlockActivation(False)
    MQ13a.SetCurrentStageID(5)

EndFunction

;=====================================================================================
;                                        PROPERTIES                                      
;=====================================================================================

int iDebrisLevel 

float fPlayerScale = 1.0
float fTimescaleBefore
int iWakeUpWatchdog ; ZP
bool bFadedBack ; ZP

bool Property bAskForLoveInterest Auto Conditional Hidden

int Property __Config_RomanceThreshold Auto
{Determines how many sympathy points the player needs to have for either Calia or Jespar in order for the other one to ask about his/her relationship to the player}

Actor Property Companion Auto Conditional Hidden

Actor Property _00E_MC_TealorRef Auto
Actor Property _00E_MC_TaranorREF Auto
Actor Property _00E_SC_AlmaREF Auto
Actor Property _00E_MC_NataraRef Auto
Actor Property _00E_MC_JesparREF Auto
Actor Property _00E_MC_CaliaREF Auto
Actor Property MQP01_FatherRef Auto
Actor Property MQ12c_SC03_FatherREF Auto
Actor Property PlayerREF Auto

GlobalVariable Property SympathyCalia Auto
GlobalVariable Property SympathyJespar Auto
GlobalVariable Property Timescale Auto
GlobalVariable Property GameHour Auto

Quest Property CQC04 Auto
Quest Property CQJ04 Auto
Quest Property MQ13a Auto

MusicType Property _00E_Music_Special_Dreams Auto
MusicType Property _00E_SilenceTransitionLowPriority Auto

Message Property _00E_MQ12c_SleepCaliaMsg Auto
Message Property _00E_MQ12c_SleepJesparMsg Auto
Message Property _00E_MQ12c_SleepJesparCaliaMsg Auto

Scene Property MQ12c_SC02_DreamGoToSleep Auto
Scene Property MQ12c_SC03_Dream Auto
Scene Property MQ12c_SC04_WakeUp Auto

Outfit Property _00E_MC_JesparOutfit Auto
Outfit Property _00E_Father_Outfit_VeryDecayed Auto

ReferenceAlias Property SC04_Companion Auto

ImageSpaceModifier Property FadeToBlackIMOD Auto
ImageSpaceModifier Property FadeToBlackBackLongImod Auto
ImageSpaceModifier Property FadeToBlackHoldImod Auto
ImageSpaceModifier Property _00E_MQ10a_DreamCollapseIMOD Auto

Formlist Property _00E_MQ12c_FireNPCs Auto
Formlist Property _00E_MQ12c_HarborNPCs Auto
Formlist Property _00E_MQ12c_SoldierNPCs Auto
Formlist Property _00E_MQ12c_PossessedNPCs Auto

ObjectReference Property MQ12c_Debris_NPC_Linker Auto
ObjectReference Property MQ12c_Debris_Smoke_Linker Auto
ObjectReference Property MQ12c_Debris_Level_01_Linker Auto
ObjectReference Property MQ12c_Debris_Level_02_Linker Auto
ObjectReference Property MQ12b_SC14_SiegeTempleMarker Auto
ObjectReference Property MQ12c_SC2_Bed Auto
ObjectReference Property PlayerStartMarkerNew Auto
ObjectReference Property MQ12c_SC3_FatherMarkerREF Auto
ObjectReference Property MQ12c_SC04_CompanionMarkerREF Auto
ObjectReference Property MQ12c_SC04_CompanionRunREF Auto
ObjectReference Property MQ12c_SC04_DoorREF Auto
ObjectReference Property MQ12c_DisableBoat Auto
ObjectReference Property MQ12c_NehrimeseScoutREF Auto
ObjectReference Property MQ12b_SC6_ArcherMarker Auto
ObjectReference Property MQ12b_SC6_HarborLinker Auto
ObjectReference Property MQ12c_GuardLinker Auto
ObjectReference Property MQ12c_WestGate_BarrierREF Auto
ObjectReference Property MQ12c_NorthGate_BarrierREF Auto
ObjectReference Property MQ12c_MyradOutsideGate_BarrierREF Auto
ObjectReference Property MQ12c_SouthGate_BarrierREF Auto
ObjectReference Property MQ12c_HarborGate_BarrierREF Auto
ObjectReference Property MQ12c_SC01_FailsaveREF Auto
ObjectReference Property MQ10a_SC1_HeartParentREF Auto
ObjectReference Property MQ12c_SC03_ForbiddenDoorREF Auto

ObjectReference Property MQ12c_SC1_ExecutionVoiceTealor001 Auto
ObjectReference Property MQ12c_SC1_ExecutionDoor001 Auto

ObjectReference Property NightLightsMarker Auto
ObjectReference Property MQ12cDebrisLight Auto