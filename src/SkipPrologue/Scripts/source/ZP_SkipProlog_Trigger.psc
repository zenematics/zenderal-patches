Scriptname ZP_SkipProlog_Trigger extends ObjectReference
{Zenderal - Skip The Prologue. Fires once on a brand-new game and deletes itself.
 Shape copied from Davipb's SkipIntro_Trigger, which is the proven archetype for this.}

Event OnTriggerEnter(ObjectReference akActionRef)

	If akActionRef == PlayerREF

		; Guard: never fire on an existing save. On a new game none of these are true.
		If !MQ01.IsRunning() && !MQ01.IsCompleted() && !SkipQuest.IsRunning() && !SkipQuest.IsCompleted()
			SkipQuest.Start()
			SkipQuest.BeginSkip()
		EndIf

		Self.Delete()
	EndIf

EndEvent

ObjectReference Property PlayerREF Auto
; Typed so we can call BeginSkip() directly. SkipIntro used a stage fragment for this; calling
; the function keeps the quest record free of QF fragment plumbing, which is awkward to
; hand-author in Spriggit YAML.
ZP_SkipProlog_Functions Property SkipQuest Auto
Quest Property MQ01 Auto
