Scriptname ZP_TheHuntEffect extends ActiveMagicEffect
{The Hunt (Prophecy, Druidic, 2026-10-29): the power's own summon effects call Triumvirate's Gray Wolf (and, with Wolf
Pack, a second), each conditioned on carrying Cost Goodberries. This effect takes the berries, plays the howl and
keeps at most MaxWolves wolves: the engine's summon limit counts every summon kind and other talents raise it
(Corpse Fever, Nature's Way, Entropy), so 3+ wolves were possible (2026-10-29). After the summons land, the
commanded actors of the wolf's race past MaxWolves are taken away, oldest first (a levelled summon's base is
generated; its race is not). Without enough Goodberries the summons do not fire and it shows a notification. The
scripted entrance that leapt the wolves in from behind was reverted the same day (Papyrus took 5-7 s in the list).}

Potion Property Goodberry Auto
Int Property Cost = 5 Auto
Sound Property Howl Auto     ; Motion Array's wolf howl (2026-10-29), as the wolves come
ActorBase Property WolfBase Auto             ; TVR_Primal_Actor_CallWolf - its race marks our wolves
Int Property MaxWolves = 2 Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	If akCaster.GetItemCount(Goodberry) < Cost
		Debug.Notification("The Hunt needs " + Cost + " Goodberries.")
		Return
	EndIf
	akCaster.RemoveItem(Goodberry, Cost, True)
	If Howl
		Howl.Play(akCaster)
	EndIf
	Utility.Wait(2.0)                           ; the summons come through their portal
	Cap(akCaster)
EndEvent

; the commanded list holds the oldest first; every wolf past the newest MaxWolves goes
Function Cap(Actor akCaster)
	Race wolfRace = WolfBase.GetRace()
	Actor[] now = PO3_SKSEFunctions.GetCommandedActors(akCaster)
	Int total = 0
	Int i = 0
	While i < now.Length
		If IsOurs(now[i], wolfRace)
			total += 1
		EndIf
		i += 1
	EndWhile
	Int excess = total - MaxWolves
	Int removed = 0
	i = 0
	While i < now.Length && removed < excess
		If IsOurs(now[i], wolfRace)
			now[i].Disable(True)
			now[i].Delete()
			removed += 1
		EndIf
		i += 1
	EndWhile
	Debug.Trace("ZP_TheHunt: " + total + " wolves, keeping " + MaxWolves + ", removed " + removed)
EndFunction

Bool Function IsOurs(Actor akActor, Race akRace)
	Return akActor && !akActor.IsDead() && !akActor.IsDisabled() && akActor.GetRace() == akRace
EndFunction
