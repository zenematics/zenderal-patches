Scriptname ZP_WhisperSoulsScript extends ActiveMagicEffect
{Whisper (Zenderal): its souls (curator 2026-11-15: "lets make it entropy spells in general" (an absorb-only build came
first: "Absorb spells charge the weapon ... in the Entropy category"); "5 souls, eyes then crystal", Soul Cleave on a
full charge, soul trap on kill). The player carries this ability while the axe is in hand (ZP_WhisperEquipScript).
- Any of the player's Entropy spells (a spell with a hostile effect whose skill is Conjuration, Enderal's Entropy:
  IsEntropy) that lands on a living enemy pulls a soul out of it along a soul stream (vanilla soul trap visuals, the
  enemy to the player) and adds a soul (Souls, GlobalVariable.Mod: thread-safe) up to Full; the last one plays
  FullSound (the curator's spooky breath). At most one soul every Gap seconds: a concentration beam or a cloak lands
  again and again. The axe adds no drain of its own (the first build did); Soul Cleave's wave is Destruction, so it
  never feeds it.
- The axe's glow follows the souls: one step of the eyes per soul, each brighter than the last, and the crystal ablaze
  at Full (Show: nodes in tools/02's mesh at scale 0, set to 1 with SKSE NetImmerse.SetNodeScale in both views). They
  are set again every Poll seconds: a weapon's 3D is rebuilt with its nodes at scale 0 on every equip, load and race
  change. Show() is Global, so the release script puts the glow out at once.
- The release on the swing (curator 2026-11-15: "make the the power attack not require a hit to trigger the wave"):
  every weapon swing of the player's is reported here (SKSE's actor action 0, registered on this effect); a swing of
  Whisper's (the source is Axe) while Souls is full and the player is power attacking (powerofthree's
  IsPowerAttacking) releases Soul Cleave at once (ZP_WhisperCleaveScript.Release), hit or miss.
powerofthree's Papyrus Extender reports the player's magic landing (OnMagicHit, registered on this effect). Each soul
writes a line to the Papyrus log ([ZP Whisper]).}

GlobalVariable Property Souls Auto
VisualEffect Property StreamVFX Auto        ; vanilla SoulTrapPVFX01 0531AF: played on the enemy, aimed at the player
VisualEffect Property GatherVFX Auto        ; vanilla SoulTrapPVFX02 0531B1: played on the player, aimed at the enemy
EffectShader Property SoulFXS Auto          ; vanilla SoulTrapTargetActFXS 054223: on the enemy
Sound Property FullSound Auto               ; ZP_WhisperChargedSound 80F: the curator's MA_MotionAudio_SpookyBreath_02
Actor Property PlayerRef Auto
Weapon Property Axe Auto                    ; Whisper 800
Spell Property Wave Auto                    ; Soul Cleave 80A
Activator Property EmptyActivator Auto      ; vanilla FXEmptyActivator 0B79FF
Sound Property ReleaseSound Auto            ; vanilla MAGMysticismSoulTrapCapture 056AC6
Sound Property PoofSound Auto               ; ZP_WhisperPoofSound 823: the curator's 02. Cartoon Poof SFX

Int Property Full = 5 AutoReadOnly          ; the souls a full charge holds (03-build-records.py SOULS, checked)
Float Property Gap = 0.75 AutoReadOnly      ; seconds between two souls at least (03-build-records.py SOUL_GAP)
Float Property Poll = 1.0 AutoReadOnly      ; the glow set again this often
Float Property StreamTime = 1.5 AutoReadOnly
Float Property ShimmerTime = 1.0 AutoReadOnly

Float lastSoul = -100.0

Event OnEffectStart(Actor akTarget, Actor akCaster)
	PO3_Events_AME.RegisterForMagicHit(self)
	RegisterForActorAction(0)                   ; weapon swings: the release
	If Souls && akTarget
		Show(akTarget, Souls.GetValueInt(), Full)
	EndIf
	RegisterForSingleUpdate(Poll)
EndEvent

Event OnUpdate()
	Actor a = GetTargetActor()
	If Souls && a
		Show(a, Souls.GetValueInt(), Full)
		RegisterForSingleUpdate(Poll)
	EndIf
EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	PO3_Events_AME.UnregisterForMagicHit(self)
	UnregisterForActorAction(0)
EndEvent

; a power attack with Whisper, full: Soul Cleave at the swing, hit or miss
Event OnActorAction(Int actionType, Actor akActor, Form source, Int slot)
	Actor thePlayer = PlayerRef
	GlobalVariable count = Souls
	If actionType != 0 || !thePlayer || akActor != thePlayer || !count || !Axe || source != Axe
		Return
	EndIf
	If count.GetValueInt() < Full || !PO3_SKSEFunctions.IsPowerAttacking(thePlayer)
		Return
	EndIf
	ZP_WhisperCleaveScript.Release(thePlayer, None, Wave, EmptyActivator, count, Full, ReleaseSound, PoofSound, GatherVFX, "the swing")
EndEvent

Event OnMagicHit(ObjectReference akTarget, Form akSource, Projectile akProjectile)
	Actor thePlayer = PlayerRef
	GlobalVariable count = Souls
	Actor foe = akTarget as Actor
	Spell s = akSource as Spell
	If !foe || !s || !thePlayer || !count || foe == thePlayer || foe.IsDead() || !foe.IsHostileToActor(thePlayer)
		Return
	EndIf
	If !IsEntropy(s)
		Return
	EndIf
	Float now = Utility.GetCurrentRealTime()
	If now - lastSoul < Gap
		Return
	EndIf
	lastSoul = now
	If StreamVFX
		StreamVFX.Play(foe, StreamTime, thePlayer)
	EndIf
	If GatherVFX
		GatherVFX.Play(thePlayer, StreamTime, foe)
	EndIf
	If SoulFXS
		SoulFXS.Play(foe, ShimmerTime)
	EndIf
	Int n = count.GetValueInt()
	If n < Full
		n = count.Mod(1.0) as Int
		If n > Full
			count.Mod(-1.0)                  ; another soul filled it in between
			n = Full
		ElseIf n == Full && FullSound
			FullSound.Play(thePlayer)
		EndIf
		Show(thePlayer, n, Full)
	EndIf
	Debug.Trace("[ZP Whisper] soul " + n + "/" + Full + " from " + s.GetName() + " on " + foe)
EndEvent

; An Entropy attack: one of its effects is hostile (flag 0x1) and of Conjuration, Enderal's Entropy.
Bool Function IsEntropy(Spell akSpell)
	Int i = 0
	Int count = akSpell.GetNumEffects()
	While i < count
		MagicEffect e = akSpell.GetNthEffectMagicEffect(i)
		If e && e.IsEffectFlagSet(0x00000001) && e.GetAssociatedSkill() == "Conjuration"
			Return True
		EndIf
		i += 1
	EndWhile
	Return False
EndFunction

; The glow at aiSouls of aiFull: the eyes' step aiSouls alone (each step is brighter than the last), the crystal at
; aiFull; in the third- and first-person 3D.
Function Show(Actor akActor, Int aiSouls, Int aiFull) Global
	Int i = 1
	While i <= aiFull
		Float s = 0.0
		If i == aiSouls
			s = 1.0
		EndIf
		String node = "ZP_WhisperSoul" + i
		NetImmerse.SetNodeScale(akActor, node, s, False)
		NetImmerse.SetNodeScale(akActor, node, s, True)
		i += 1
	EndWhile
	Float blaze = 0.0
	If aiSouls >= aiFull
		blaze = 1.0
	EndIf
	NetImmerse.SetNodeScale(akActor, "ZP_WhisperBlaze", blaze, False)
	NetImmerse.SetNodeScale(akActor, "ZP_WhisperBlaze", blaze, True)
EndFunction
