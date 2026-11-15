Scriptname ZP_ArgentVerdictSmiteScript extends ActiveMagicEffect
{Argent Verdict (Zenderal): the release, version 3 (curator 2026-11-14: "Keep the 4 knuckle motes / instead of the
Chain lightning, smite 4 enemies in proximity to the player on charged power attack. the smite beams come from the sky
like regular smite. but the effect is like the effect from the picture (I believe this is the Absolution spell in
Dark hierohant)"). Hits light the four knuckle motes (ZP_ArgentVerdictChargeScript); the hammer's enchantment starts
this on the enemy a power attack hits while Charges is full (its conditions).
- It claims the charges (GlobalVariable.Mod, thread-safe: a second release finds none), spends ManaCost of the
  player's Mana (curator 2026-11-15: "each power attack smite requires 20 mana"; the enchantment already refuses a
  release below it, and a player who spent it in between gets the charges back) and puts the motes out.
- Up to Targets enemies: the struck one, then the nearest others within Radius of the player (powerofthree's
  FindAllReferencesOfFormType; living, hostile to the player, not the player's teammates).
- Over each, Stagger apart, a smite beam (BeamBase: tools/03's VerdictSmiteBeam.nif, Kittytail's Absolution beam stood
  on end, her rune circle at its top) is placed BeamLength above the enemy's feet, so its strips run down onto it.
  The curator's church bell rings once.
- LandDelay after each beam appears: the impact (Impact: Kittytail's impact in white and black, with the strike's
  sound) at the enemy's feet and the strike (Strike: Health, Stamina and Magicka damage, Kittytail's white glow,
  undead double) through DoCombatSpellApply, blamed on the player.
- The impact places the orb spawner (its PlacedObject, ACTI 860, ZP_ArgentVerdictOrbSpawnerScript), which scatters the
  beam's orbs, as Prophecy's Smite does. Each step writes a line to the Papyrus log ([ZP Argent release]).
- Each beam vanishes Linger after its own strike (Disable without fade, then Delete): the curator's first test (2026-11-14:
  "the beams last for too long they should strike and then disappear") had them stand 1.2 s and fade 1 s more; then
  "the beams could stay a little longer" (0.2 s was the first fix).
The struck enemy's beam is placed first, before the search for the others, the bell and the motes (curator
2026-11-14: "the Smite itself is triggered a bit late after the power attack, can we make it almost instant?"), even
on a corpse the blow killed (its spot is smitten, its orbs fly; the dead take no damage). The three steps run on one
clock (GetCurrentRealTime), so every beam keeps its own timing. The effect has no duration, so everything after the first lines runs on locals.}

Activator Property BeamBase Auto
Explosion Property Impact Auto
Spell Property Strike Auto
Sound Property BellSound Auto
GlobalVariable Property Charges Auto
Actor Property PlayerRef Auto

Int Property Knuckles = 4 AutoReadOnly               ; the motes (02-build-records.py KNUCKLES)
Int Property Hits = 8 AutoReadOnly                   ; the charges a release takes (02-build-records.py HITS)
Float Property ManaCost = 20.0 AutoReadOnly          ; 02-build-records.py MANA_COST (the enchantment's condition)
Int Property Targets = 4 AutoReadOnly                ; 02-build-records.py TARGETS (the item card)
Float Property Radius = 800.0 AutoReadOnly           ; round the player
Float Property BeamLength = 1024.0 AutoReadOnly      ; tools/03 BEAM_LENGTH (checked): the circle to the strips' end
Float Property Stagger = 0.1 AutoReadOnly            ; between beams
Float Property LandDelay = 0.1 AutoReadOnly          ; a beam's strips reach the ground (0.3 until "a bit late")
Float Property Linger = 0.6 AutoReadOnly             ; after its strike, then gone at once (0.2 until "a little longer")

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Activator beamForm = BeamBase
	Explosion impactFX = Impact
	Spell strikeSpell = Strike
	Sound bellFX = BellSound
	GlobalVariable charge = Charges
	Actor thePlayer = PlayerRef
	Int motes = Knuckles
	Int full = Hits
	Float cost = ManaCost
	Int most = Targets
	Float reach = Radius
	Float height = BeamLength
	Float gap = Stagger
	Float land = LandDelay
	Float after = Linger
	If !akTarget || !beamForm || !strikeSpell || !charge || !thePlayer || akTarget == thePlayer || akCaster != thePlayer
		Return
	EndIf
	; claim the charges
	If charge.Mod(-full as Float) < 0.0
		charge.Mod(full as Float)            ; another release took them
		Return
	EndIf
	; and the Mana
	If thePlayer.GetActorValue("Magicka") < cost
		charge.Mod(full as Float)            ; spent since the hit: keep the charge
		Debug.Trace("[ZP Argent release] not enough Mana")
		Return
	EndIf
	thePlayer.DamageActorValue("Magicka", cost)
	; the struck enemy's beam at once, then the rest
	Actor[] foes = new Actor[8]
	ObjectReference[] beams = new ObjectReference[8]
	Float start = Utility.GetCurrentRealTime()
	foes[0] = akTarget
	beams[0] = akTarget.PlaceAtMe(beamForm, 1, False, True)
	beams[0].SetAngle(0.0, 0.0, 0.0)
	beams[0].SetPosition(akTarget.GetPositionX(), akTarget.GetPositionY(), akTarget.GetPositionZ() + height)
	beams[0].Enable(False)
	Int count = 1
	Int placed = 1
	Utility.Wait(land)                       ; it strikes before anything else runs
	If impactFX
		akTarget.PlaceAtMe(impactFX)         ; its PlacedObject scatters the orbs
	EndIf
	If !akTarget.IsDead()
		thePlayer.DoCombatSpellApply(strikeSpell, akTarget)
	EndIf
	Int struck = 1
	If bellFX
		bellFX.Play(thePlayer)
	EndIf
	ZP_ArgentVerdictMotesScript.Show(thePlayer, 0, motes)
	Debug.Trace("[ZP Argent release] charges claimed, struck " + akTarget)
	; the others: the nearest round the player, in one pass over the actors near (the first build looked them over once
	; for each beam and took 1-2 s in the curator's log before any beam appeared)
	ObjectReference[] near = PO3_SKSEFunctions.FindAllReferencesOfFormType(thePlayer, 62, reach)   ; 62 = Character
	Actor[] cand = new Actor[32]
	Float[] dist = new Float[32]
	Int nc = 0
	Int i = 0
	While near && i < near.Length && nc < cand.Length
		Actor a = near[i] as Actor
		If a && a != thePlayer && a != akTarget && a.IsHostileToActor(thePlayer) && !a.IsDead()
			cand[nc] = a
			dist[nc] = a.GetDistance(thePlayer)
			nc += 1
		EndIf
		i += 1
	EndWhile
	While count < most && nc > 0
		Int best = -1
		Int k = 0
		While k < nc
			If cand[k] && (best < 0 || dist[k] < dist[best])
				best = k
			EndIf
			k += 1
		EndWhile
		If best < 0
			most = count                     ; no more
		Else
			foes[count] = cand[best]
			cand[best] = None
			count += 1
		EndIf
	EndWhile
	Debug.Trace("[ZP Argent release] " + count + " enemies")
	; one clock, restarted now so beam 1 is due at once: beam k appears at k * gap, strikes at k * gap + land, vanishes
	; at k * gap + land + after (beam 0 already struck; it vanishes `after` from here)
	Int gone = 0
	start = Utility.GetCurrentRealTime() - gap
	While gone < count
		Float now = Utility.GetCurrentRealTime() - start
		If placed < count && now >= placed * gap
			Actor foe = foes[placed]
			ObjectReference beam = foe.PlaceAtMe(beamForm, 1, False, True)
			beam.SetAngle(0.0, 0.0, 0.0)
			beam.SetPosition(foe.GetPositionX(), foe.GetPositionY(), foe.GetPositionZ() + height)
			beam.Enable(False)
			beams[placed] = beam
			placed += 1
		ElseIf struck < placed && now >= struck * gap + land
			Actor hit = foes[struck]
			If impactFX
				hit.PlaceAtMe(impactFX)                ; its PlacedObject scatters the orbs
			EndIf
			Debug.Trace("[ZP Argent release] beam " + struck + " struck " + hit + " (beam " + beams[struck] + ")")
			If !hit.IsDead()
				thePlayer.DoCombatSpellApply(strikeSpell, hit)
			EndIf
			struck += 1
		ElseIf gone < struck && now >= gone * gap + land + after
			beams[gone].Disable(False)
			beams[gone].Delete()
			gone += 1
		Else
			Utility.Wait(0.02)
		EndIf
	EndWhile
EndEvent
