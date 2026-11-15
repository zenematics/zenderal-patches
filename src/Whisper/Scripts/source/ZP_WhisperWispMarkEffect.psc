Scriptname ZP_WhisperWispMarkEffect extends ActiveMagicEffect
{Whisper (Zenderal): the soul wisp (curator 2026-11-15: "if the wave kills an enemy, let it spawn a purple wisp", "Fights
for you", "the wisp lasts for 30 seconds, only 1 wisp at a time"). Rides on a hidden 1 s mark Soul Cleave's wave puts on
every enemy it hits (directly or in its cone), which survives death. When the mark ends on a corpse - vanilla's soul
trap test, as Midnight Sting's brood: OnEffectFinish, then IsDead - a Soul Wisp rises from it: Enderal's Wisp in
purple, a short-lived ally placed the way Prophecy's Legion of the Damned places its skeletons (PlaceActorAtMe,
teammate; its own ability, ZP_WhisperWispEffect, ends it after 30 s and sends it after enemies).
One wisp at a time: a new wisp replaces the one out (it fades away), unless a wisp rose within the last FreshSeconds
(one wave that kills several raises one wisp). Wisps holds the wisps out; each stamps the game time it rose into its
Variable08. Each wisp writes a line to the Papyrus log ([ZP Whisper wisp]). Needs powerofthree's Papyrus Extender.}

ActorBase Property Wisp Auto                ; ZP_WhisperWisp 815
FormList Property Wisps Auto                ; ZP_WhisperWisps 814
Actor Property PlayerRef Auto

Float Property FreshSeconds = 2.0 AutoReadOnly
Float Property BaseHealth = 40.0 AutoReadOnly
Float Property HealthPerLevel = 4.0 AutoReadOnly
Float Property SeekRadius = 2500.0 AutoReadOnly
Int Property kActorCharacter = 62 AutoReadOnly

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	Actor player = PlayerRef
	If !akTarget || !player || akCaster != player || akTarget == player || !akTarget.IsDead() || !Wisp || !Wisps
		Return
	EndIf
	Float now = Utility.GetCurrentGameTime()
	Float timescale = (Game.GetForm(0x3A) as GlobalVariable).GetValue()     ; TimeScale
	Float fresh = FreshSeconds * timescale / 86400.0
	; a wisp that rose within FreshSeconds stays (one wave, one wisp); any other is replaced
	Int i = Wisps.GetSize()
	While i > 0
		i -= 1
		Actor w = Wisps.GetAt(i) as Actor
		If w && !w.IsDead() && !w.IsDisabled() && now - w.GetActorValue("Variable08") < fresh
			Return
		EndIf
	EndWhile
	Actor risen = akTarget.PlaceActorAtMe(Wisp)
	If !risen
		Return
	EndIf
	risen.SetActorValue("Variable08", now)
	risen.SetActorValue("Health", BaseHealth + HealthPerLevel * player.GetLevel())
	risen.RestoreActorValue("Health", 100000.0)
	risen.SetPlayerTeammate(true)
	i = Wisps.GetSize()
	While i > 0                                   ; the wisp out fades away
		i -= 1
		Form f = Wisps.GetAt(i)
		Actor old = f as Actor
		If old && old != risen
			Wisps.RemoveAddedForm(f)
			If !old.IsDisabled()
				old.Disable(True)
			EndIf
			old.Delete()
		ElseIf !old && f
			Wisps.RemoveAddedForm(f)
		EndIf
	EndWhile
	Wisps.AddForm(risen)
	Actor foe = Nearest(risen, player)
	If foe
		risen.StartCombat(foe)
	EndIf
	Debug.Trace("[ZP Whisper wisp] " + risen + " rose from " + akTarget + ", after " + foe)
EndEvent

Actor Function Nearest(Actor akFrom, Actor akPlayer)
	ObjectReference[] near = PO3_SKSEFunctions.FindAllReferencesOfFormType(akFrom, kActorCharacter, SeekRadius)
	Actor best = None
	Float bestDistance = 1000000.0
	Int i = 0
	While near && i < near.Length
		Actor a = near[i] as Actor
		If a && a != akFrom && !a.IsDead() && a.IsHostileToActor(akPlayer)
			Float d = akFrom.GetDistance(a)
			If d < bestDistance
				bestDistance = d
				best = a
			EndIf
		EndIf
		i += 1
	EndWhile
	Return best
EndFunction
