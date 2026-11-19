Scriptname ZP_OwlBowQuiverEffect extends ActiveMagicEffect
{Owl Bow (Zenderal): on the player while the bow is equipped. The endless quiver (Refill); the draw sound, one of
three air swells in turn, started on arrowAttach (cut to peak at BowDrawn), stopped on a cancelled draw or the next
draw; on the shot a wing beat, or on every 5th shot the owl's hoot and a guaranteed critical hit (CritReady = 1
until the next shot; perk CritPerk reads it). Setup() repairs an effect carried over in a save from an older build.}

Ammo Property IceArrow Auto
Sound Property ReleaseHoot Auto
Sound Property DrawAir1 Auto
Sound Property DrawAir2 Auto
Sound Property DrawAir3 Auto
Sound Property ShotFlap Auto
GlobalVariable Property CritReady Auto
Perk Property CritPerk Auto
Int Property CritEvery = 5 AutoReadOnly
Int Property Stock = 50 AutoReadOnly

Actor wielder
Int setupVersion = 0
Int airID = 0
Int airNext = 0
Bool drawing = False
Int shots = 0

Event OnEffectStart(Actor akTarget, Actor akCaster)
	wielder = akTarget
	Setup()
	Refill()
EndEvent

; an effect already running when a save was made keeps that build's registrations and property values
; (2026-11-17: every Sound was None), so every event checks this first
Function Setup()
	If setupVersion >= 5
		Return
	EndIf
	setupVersion = 5
	If !wielder
		wielder = GetTargetActor()
	EndIf
	UnregisterForAnimationEvent(wielder, "bowDrawStart")
	UnregisterForAnimationEvent(wielder, "bowDrawn")
	RegisterForAnimationEvent(wielder, "arrowRelease")
	RegisterForAnimationEvent(wielder, "BowDraw")
	RegisterForAnimationEvent(wielder, "arrowAttach")
	RegisterForAnimationEvent(wielder, "bowReset")
	If !ReleaseHoot
		ReleaseHoot = Game.GetFormFromFile(0x811, "Zenderal - Owl Bow.esp") as Sound
	EndIf
	If !DrawAir1
		DrawAir1 = Game.GetFormFromFile(0x813, "Zenderal - Owl Bow.esp") as Sound
	EndIf
	If !DrawAir2
		DrawAir2 = Game.GetFormFromFile(0x815, "Zenderal - Owl Bow.esp") as Sound
	EndIf
	If !DrawAir3
		DrawAir3 = Game.GetFormFromFile(0x817, "Zenderal - Owl Bow.esp") as Sound
	EndIf
	If !ShotFlap
		ShotFlap = Game.GetFormFromFile(0x819, "Zenderal - Owl Bow.esp") as Sound
	EndIf
	If !CritReady
		CritReady = Game.GetFormFromFile(0x81A, "Zenderal - Owl Bow.esp") as GlobalVariable
	EndIf
	If !CritPerk
		CritPerk = Game.GetFormFromFile(0x81B, "Zenderal - Owl Bow.esp") as Perk
	EndIf
	If CritPerk && !wielder.HasPerk(CritPerk)
		wielder.AddPerk(CritPerk)
	EndIf
EndFunction

Event OnAnimationEvent(ObjectReference akSource, String asEventName)
	Setup()
	If asEventName == "arrowAttach"
		StopAir()
		drawing = True
		Sound s = DrawAir1
		If airNext == 1
			s = DrawAir2
		ElseIf airNext == 2
			s = DrawAir3
		EndIf
		airNext = (airNext + 1) % 3
		airID = s.Play(wielder)
	ElseIf asEventName == "bowReset"
		If drawing
			StopAir()
		EndIf
		drawing = False
	ElseIf asEventName == "arrowRelease"
		drawing = False
		shots += 1
		If shots >= CritEvery
			shots = 0
			CritReady.SetValue(1)
			ReleaseHoot.Play(wielder)
		Else
			CritReady.SetValue(0)
			ShotFlap.Play(wielder)
		EndIf
		RegisterForSingleUpdate(0.25)
	ElseIf asEventName == "BowDraw"
		RegisterForSingleUpdate(0.25)
	EndIf
EndEvent

Function StopAir()
	If airID
		Sound.StopInstance(airID)
		airID = 0
	EndIf
EndFunction

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	StopAir()
	If CritReady
		CritReady.SetValue(0)
	EndIf
EndEvent

Event OnUpdate()
	Refill()
EndEvent

Function Refill()
	If !wielder
		Return
	EndIf
	Int n = wielder.GetItemCount(IceArrow)
	If n < Stock
		wielder.AddItem(IceArrow, Stock - n, True)
	EndIf
	If !wielder.IsEquipped(IceArrow)
		wielder.EquipItem(IceArrow, False, True)
	EndIf
EndFunction
