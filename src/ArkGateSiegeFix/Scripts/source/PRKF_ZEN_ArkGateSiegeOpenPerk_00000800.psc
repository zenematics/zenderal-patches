;BEGIN FRAGMENT CODE - Do not edit anything between this and the end comment
;NEXT FRAGMENT INDEX 2
Scriptname PRKF_ZEN_ArkGateSiegeOpenPerk_00000800 Extends Perk Hidden

;BEGIN FRAGMENT Fragment_1
Function Fragment_1(ObjectReference akTargetRef, Actor akActor)
;BEGIN CODE
; Default processing only: skips the OnActivate of the lock script a save may still carry on the gate
; and opens it even with activation blocked, as that script itself does for doors it lets through.
akTargetRef.Activate(akActor, True)
;END CODE
EndFunction
;END FRAGMENT

;END FRAGMENT CODE - Do not edit anything between this and the begin comment
