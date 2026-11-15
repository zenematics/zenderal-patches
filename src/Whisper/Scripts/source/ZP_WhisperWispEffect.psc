Scriptname ZP_WhisperWispEffect extends ActiveMagicEffect
{Whisper (Zenderal): a Soul Wisp's own ability (ActorEffect on its NPC record; ZP_WhisperWispMarkEffect raises the
wisp). Midnight Sting's spiderling effect (ZP_StingSpiderlingEffect) for a wisp:
- its glow: GlowFX (Enderal's Wisp glow in purple, tools/06) played on it once its 3D is in, as vanilla's
  FXWitchlightAttachSCRIPT plays the Wisp's own (its race copy leaves the blue one off);
- its whisper (curator 2026-11-15: "add this whisper sound effect looped for when the Wisp is active", their licensed
  MA_MotionAudio_GhostWhispering_03.wav, tools/04): LoopSound, a looping positional sound, played on it with its glow
  and stopped whenever it goes;
- its life (curator: "the wisp lasts for 30 seconds"): the first time it starts it stamps the game time it ends at
  into Variable07 (LifeSeconds of real time at the current TimeScale, so a load does not reset it), checks the clock
  every PollSeconds and fades away when its time is up;
- one at a time ("only 1 wisp at a time"): ZP_WhisperWispMarkEffect fades the old wisp when a new one rises; should two
  rise at once, a wisp that finds a newer one in Wisps (a later Variable08) fades itself;
- the hunt: whenever it has no live hostile target it goes for the nearest enemy of the player within SeekRadius;
- its burst (curator: "If you hit the Wisp with an Entropy spell it explodes reducing enemies magic resistance by 15%
  and gives 30 mana to the player"): the player's Entropy spell striking it (OnHit with a spell, or one of its hostile
  Conjuration effects landing: OnMagicEffectApply; Entropy is Enderal's Conjuration) bursts it at once: BurstFX (the
  wisp's death flash in purple, tools/06) where it was, Rupture (magic resistance -15 for 15 s, the soul trap shimmer)
  on every living actor hostile to the player within BurstRadius, blamed on the player, and ManaGain Magicka back to
  the player along a soul stream;
- killed otherwise, it leaves Wisps and fades 2 s later (it waits a moment first: a killing Entropy spell's hit may
  still be on its way, and then it bursts).
Each step logs [ZP Whisper wisp]. Needs powerofthree's Papyrus Extender.}

FormList Property Wisps Auto                ; ZP_WhisperWisps 814
VisualEffect Property GlowFX Auto           ; ZP_WhisperWispFX 81B
Sound Property LoopSound Auto               ; ZP_WhisperWispLoopSound 821: the curator's ghost whispering, looping
Spell Property Rupture Auto                 ; ZP_WhisperWispRupture 81E: magic resistance -15
Explosion Property BurstFX Auto             ; ZP_WhisperWispBurst 81F: the purple flash, harmless
VisualEffect Property StreamVFX Auto        ; vanilla SoulTrapPVFX01 0531AF: on the wisp, aimed at the player
VisualEffect Property GatherVFX Auto        ; vanilla SoulTrapPVFX02 0531B1: on the player, aimed at the wisp

Float Property LifeSeconds = 30.0 AutoReadOnly       ; 03-build-records.py WISP_LIFE (checked there)
Float Property ManaGain = 30.0 AutoReadOnly          ; 03-build-records.py WISP_MANA (checked there)
Float Property BurstRadius = 400.0 AutoReadOnly      ; 03-build-records.py WISP_BURST_RADIUS (checked there)
Float Property PollSeconds = 0.5 AutoReadOnly
Float Property SeekRadius = 2500.0 AutoReadOnly
Int Property kActorCharacter = 62 AutoReadOnly

Actor me
Bool gone = False
Int loopId = 0

Event OnEffectStart(Actor akTarget, Actor akCaster)
	me = akTarget
	If !me || me.IsDead()
		Return
	EndIf
	If me.GetActorValue("Variable07") <= 0.0
		Float timescale = (Game.GetForm(0x3A) as GlobalVariable).GetValue()     ; TimeScale
		me.SetActorValue("Variable07", Utility.GetCurrentGameTime() + LifeSeconds * timescale / 86400.0)
	EndIf
	RegisterForSingleUpdate(PollSeconds)
	Int wait = 50                                        ; the glow and the whisper once the 3D is in
	While !me.Is3DLoaded() && wait > 0
		Utility.Wait(0.1)
		wait -= 1
	EndWhile
	If gone || me.IsDead()
		Return
	EndIf
	If GlowFX && me.Is3DLoaded()
		GlowFX.Play(me, -1.0)
	EndIf
	If LoopSound && loopId == 0
		loopId = LoopSound.Play(me)
	EndIf
EndEvent

Event OnUpdate()
	If !me || me.IsDead() || gone
		Return
	EndIf
	If Utility.GetCurrentGameTime() >= me.GetActorValue("Variable07")
		FadeAway("its time is up")
		Return
	EndIf
	RegisterForSingleUpdate(PollSeconds)                 ; first: an error below must not end the clock
	If Newer()
		FadeAway("a newer wisp rose")
		Return
	EndIf
	Seek()
EndEvent

; the player's Entropy spell strikes it
Event OnHit(ObjectReference akAggressor, Form akSource, Projectile akProjectile, Bool abPowerAttack, Bool abSneakAttack, Bool abBashAttack, Bool abHitBlocked)
	Spell s = akSource as Spell
	If !gone && s && akAggressor == Game.GetPlayer() && IsEntropySpell(s)
		Burst(s.GetName())
	EndIf
EndEvent

Event OnMagicEffectApply(ObjectReference akCaster, MagicEffect akEffect)
	If !gone && akEffect && akCaster == Game.GetPlayer() && IsEntropyEffect(akEffect)
		Burst(akEffect.GetName())
	EndIf
EndEvent

; another wisp out rose after this one
Bool Function Newer()
	Float mine = me.GetActorValue("Variable08")
	Int i = Wisps.GetSize()
	While i > 0
		i -= 1
		Actor w = Wisps.GetAt(i) as Actor
		If w && w != me && !w.IsDead() && !w.IsDisabled() && w.GetActorValue("Variable08") > mine
			Return True
		EndIf
	EndWhile
	Return False
EndFunction

; no live hostile target: straight at the nearest enemy of the player
Function Seek()
	Actor player = Game.GetPlayer()
	Actor current = me.GetCombatTarget()
	If current && !current.IsDead() && current.IsHostileToActor(player)
		Return
	EndIf
	ObjectReference[] near = PO3_SKSEFunctions.FindAllReferencesOfFormType(me, kActorCharacter, SeekRadius)
	Actor best = None
	Float bestDistance = 1000000.0
	Int i = 0
	While near && i < near.Length
		Actor a = near[i] as Actor
		If a && a != me && !a.IsDead() && a.IsHostileToActor(player)
			Float d = me.GetDistance(a)
			If d < bestDistance
				bestDistance = d
				best = a
			EndIf
		EndIf
		i += 1
	EndWhile
	If best
		me.StartCombat(best)
	EndIf
EndFunction

Function Burst(String asBy)
	If gone || !me
		Return
	EndIf
	gone = True
	Wisps.RemoveAddedForm(me)
	Actor player = Game.GetPlayer()
	If BurstFX
		me.PlaceAtMe(BurstFX)
	EndIf
	Int hit = 0
	ObjectReference[] near = PO3_SKSEFunctions.FindAllReferencesOfFormType(me, kActorCharacter, BurstRadius)
	Int i = 0
	While Rupture && near && i < near.Length
		Actor a = near[i] as Actor
		If a && a != me && a != player && !a.IsDead() && a.IsHostileToActor(player)
			Rupture.RemoteCast(player, player, a)
			hit += 1
		EndIf
		i += 1
	EndWhile
	player.RestoreActorValue("Magicka", ManaGain)
	If StreamVFX
		StreamVFX.Play(me, 1.0, player)
	EndIf
	If GatherVFX
		GatherVFX.Play(player, 1.0, me)
	EndIf
	Debug.Trace("[ZP Whisper wisp] " + me + " burst by " + asBy + ": " + hit + " enemies' magic resistance lowered, " + (ManaGain as Int) + " Magicka to the player")
	Quiet()
	me.Disable(False)
	me.Delete()
EndFunction

Function FadeAway(String asWhy)
	If gone
		Return
	EndIf
	gone = True
	Wisps.RemoveAddedForm(me)
	Debug.Trace("[ZP Whisper wisp] " + me + " fades away: " + asWhy)
	Quiet()
	If !me.IsDisabled()
		me.Disable(True)
	EndIf
	me.Delete()
EndFunction

; its glow and its whisper off
Function Quiet()
	If GlowFX && me
		GlowFX.Stop(me)
	EndIf
	If loopId != 0
		Sound.StopInstance(loopId)
		loopId = 0
	EndIf
EndFunction

Event OnDying(Actor akKiller)
	Utility.Wait(0.3)                                    ; a killing Entropy spell's hit: it bursts instead
	If gone
		Return
	EndIf
	gone = True
	Wisps.RemoveAddedForm(me)
	Debug.Trace("[ZP Whisper wisp] " + me + " killed by " + akKiller)
	Utility.Wait(1.7)
	Quiet()
	If !me.IsDisabled()
		me.Disable(True)
	EndIf
	me.Delete()
EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	Quiet()
EndEvent

; Entropy: a hostile effect (flag 0x1) of Conjuration, Enderal's Entropy (the souls script's test)
Bool Function IsEntropyEffect(MagicEffect akEffect) Global
	Return akEffect.IsEffectFlagSet(0x00000001) && akEffect.GetAssociatedSkill() == "Conjuration"
EndFunction

Bool Function IsEntropySpell(Spell akSpell) Global
	Int i = 0
	Int count = akSpell.GetNumEffects()
	While i < count
		MagicEffect e = akSpell.GetNthEffectMagicEffect(i)
		If e && IsEntropyEffect(e)
			Return True
		EndIf
		i += 1
	EndWhile
	Return False
EndFunction
