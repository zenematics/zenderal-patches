Scriptname ZP_CalderaEruptionScript extends ActiveMagicEffect
{Caldera (Zenderal): the eruption. Started by 81C on the player (the swing: ZP_CalderaTiersScript casts it on a
full-charge power attack, hit or miss; it erupts under the enemy swung at, FoeInFront, or Ahead in front of the
player) or by 806 on a struck enemy (the enchantment's fallback). It claims the charges, spends ManaCost Mana (none:
the charges stay), sets the fire damage from Elementalism, finds the ground with ZP_Aim.GroundBelow, bursts the ring
of fire and the blast, places the volcano, opens Vents small volcanoes round it and plays the lava river. Logs
[ZP Caldera eruption]. Everything is read into locals first: an instant effect is gone before the volcanoes are.
KEEP THIS DOCSTRING SHORT: the game's script loader crashes on a .pex string over ~4 KB (this one was 4407 bytes on
2026-11-16); 02-build-records.py checks it. The full story is in arch-docs/patches/Caldera.md.}

Explosion Property Shockwave Auto
Explosion Property Volcano Auto
Activator Property Vent Auto
Sound Property LavaLoop Auto
Static Property GroundMarker Auto                    ; XMarkerHeading 000034
Spell Property Blast Auto
Spell Property LavaBomb Auto
GlobalVariable Property Charges Auto
Actor Property PlayerRef Auto

Int Property Tiers = 5 AutoReadOnly                  ; tools/01-build-mesh.py TIERS
Int Property Hits = 8 AutoReadOnly                   ; 02-build-records.py HITS
Float Property ManaCost = 20.0 AutoReadOnly          ; 02-build-records.py MANA_COST (checked; the fallback's condition)
Float Property ShockRadius = 350.0 AutoReadOnly      ; tools/01-build-mesh.py scales the ring to it (checked)
Float Property SoundLife = 7.0 AutoReadOnly          ; 02-build-records.py ERUPT + 1 (checked)
Float Property BlastBase = 22.5 AutoReadOnly         ; 02-build-records.py BLAST (checked): 22.5 at 0, 67.5 at 100
Float Property BlastPerPoint = 0.45 AutoReadOnly
Float Property BombBase = 7.5 AutoReadOnly           ; 02-build-records.py BOMB (checked): 7.5 at 0, 26.5 at 100
Float Property BombPerPoint = 0.19 AutoReadOnly
Float Property SkillCap = 100.0 AutoReadOnly
Float Property FrontReach = 260.0 AutoReadOnly       ; the enemy swung at: the nearest living enemy this close
Float Property FrontArc = 50.0 AutoReadOnly          ; and within this many degrees of the player's heading
Float Property Ahead = 110.0 AutoReadOnly            ; with none, the eruption goes this far in front of the player
Float Property AheadUp = 96.0 AutoReadOnly           ; the ray in front starts this far above the player's feet
Float Property AheadDrop = 128.0 AutoReadOnly        ; ground in front further below the player's feet is a ledge
Float Property GroundUp = 24.0 AutoReadOnly          ; the ray starts this far above the enemy's position (a table
Float Property GroundDown = 2048.0 AutoReadOnly      ; or arch over a standing enemy's head is never ground)
Float Property GroundUpRagdoll = 64.0 AutoReadOnly   ; over a dead or knocked-down enemy (its position rides its body)
Int Property Vents = 5 AutoReadOnly                  ; small volcanoes an eruption
Float Property VentNear = 170.0 AutoReadOnly         ; their distance from the volcano (its cone is ~90 across)
Float Property VentFar = 420.0 AutoReadOnly
Float Property VentSpread = 20.0 AutoReadOnly        ; degrees either way off its share of the circle
Float Property VentClimb = 0.6 AutoReadOnly          ; outdoors a vent's ray starts 48 + this x its distance above the
Float Property VentClimbIndoors = 0.25 AutoReadOnly  ; volcano's ground (a 30-degree slope; indoors 14 degrees)
Float Property VentDrop = 0.6 AutoReadOnly           ; ground more than 48 + this x its distance below the volcano's
Float Property VentGapMin = 0.15 AutoReadOnly        ; is a ledge: no vent. Seconds between two vents
Float Property VentGapMax = 0.4 AutoReadOnly

Event OnEffectStart(Actor akTarget, Actor akCaster)
	; everything into locals: an instant effect is gone long before the small volcanoes are
	Explosion ring = Shockwave
	Explosion eruption = Volcano
	Activator ventForm = Vent
	Sound lava = LavaLoop
	Static marker = GroundMarker
	Spell blastSpell = Blast
	Spell bombSpell = LavaBomb
	GlobalVariable charge = Charges
	Actor thePlayer = PlayerRef
	Int full = Hits
	Int tierCount = Tiers
	Float cost = ManaCost
	Float reach = ShockRadius
	Float soundFor = SoundLife
	Float down = GroundDown
	Int ventCount = Vents
	Float ventNearest = VentNear
	Float ventFurthest = VentFar
	Float spread = VentSpread
	Float drop = VentDrop
	Float gapMin = VentGapMin
	Float gapMax = VentGapMax
	If !akTarget || !charge || !thePlayer || akCaster != thePlayer
		Return
	EndIf
	; who it erupts under: the struck enemy, or on the swing the enemy in front (or none)
	Actor foe = akTarget
	String by = "the hit"
	If akTarget == thePlayer
		foe = FoeInFront(thePlayer, FrontReach, FrontArc)
		by = "the swing"
	EndIf
	; claim the charges
	If charge.Mod(-full as Float) < 0.0
		charge.Mod(full as Float)            ; another release took them
		Return
	EndIf
	; and the Mana
	Float mana = thePlayer.GetActorValue("Magicka")
	If mana < cost
		charge.Mod(full as Float)            ; not enough: keep the charge
		Debug.Trace("[ZP Caldera eruption] " + by + ": not enough Mana (" + mana + " of " + cost + "), the charge kept")
		Return
	EndIf
	thePlayer.DamageActorValue("Magicka", cost)
	ZP_CalderaTiersScript.Show(thePlayer, 0, tierCount)
	; the damage by Elementalism, before anything is cast
	Float skill = thePlayer.GetActorValue("Destruction")
	If skill > SkillCap
		skill = SkillCap
	ElseIf skill < 0.0
		skill = 0.0
	EndIf
	Float blastDamage = BlastBase + BlastPerPoint * skill
	Float bombDamage = BombBase + BombPerPoint * skill
	If blastSpell
		blastSpell.SetNthEffectMagnitude(0, blastDamage)
	EndIf
	If bombSpell
		bombSpell.SetNthEffectMagnitude(0, bombDamage)
	EndIf
	; where: the ground under the enemy, or in front of the player
	Float gx
	Float gy
	Float standZ
	Float up
	String where
	If foe
		gx = foe.GetPositionX()
		gy = foe.GetPositionY()
		standZ = foe.GetPositionZ()
		up = GroundUp
		If foe.IsDead() || PO3_SKSEFunctions.GetActorKnockState(foe) != 0
			up = GroundUpRagdoll
		EndIf
		where = "under " + foe + " (dead " + foe.IsDead() + ")"
	Else
		Float heading = thePlayer.GetAngleZ()
		gx = thePlayer.GetPositionX() + Ahead * Math.Sin(heading)
		gy = thePlayer.GetPositionY() + Ahead * Math.Cos(heading)
		standZ = thePlayer.GetPositionZ()
		up = AheadUp
		where = "in front of the player"
	EndIf
	Float gz = standZ
	String how = "no ground found, its own height"
	ObjectReference spot = None
	If marker
		spot = thePlayer.PlaceAtMe(marker, 1, False, False)
		spot.SetAngle(0.0, 0.0, thePlayer.GetAngleZ())
		spot.SetPosition(gx, gy, standZ)
		Float ground = GroundUnder(spot, up, down)
		If !foe && ground > NoGround() && ground < standZ - AheadDrop
			; a ledge in front: under the player instead
			gx = thePlayer.GetPositionX()
			gy = thePlayer.GetPositionY()
			spot.SetPosition(gx, gy, standZ)
			ground = GroundUnder(spot, GroundUp, down)
			where = "under the player (a drop in front)"
		EndIf
		If ground > NoGround()
			gz = ground
			how = "ground"
		EndIf
		spot.SetPosition(gx, gy, gz)
	EndIf
	ObjectReference at = spot
	If !at
		at = foe
	EndIf
	If !at
		at = thePlayer
	EndIf
	If ring
		at.PlaceAtMe(ring)
	EndIf
	If eruption
		at.PlaceAtMe(eruption)               ; its PlacedObject raises the volcano
	EndIf
	Int lavaSound = 0
	If lava
		lavaSound = lava.Play(at)
	EndIf
	Int hit = 0
	If blastSpell
		ObjectReference[] near = PO3_SKSEFunctions.FindAllReferencesOfFormType(at, 62, reach)   ; 62 = Character
		Int i = 0
		While near && i < near.Length
			Actor other = near[i] as Actor
			If other && other != thePlayer && !other.IsDead() && other.IsHostileToActor(thePlayer)
				thePlayer.DoCombatSpellApply(blastSpell, other)
				hit += 1
			EndIf
			i += 1
		EndWhile
	EndIf
	Debug.Trace("[ZP Caldera eruption] on " + by + ", " + where + ": z " + standZ + " -> " + gz + " (" + how + "), " + cost + " Mana spent, Elementalism " + skill + ": blast " + blastDamage + " on " + hit + " enemies, bombs " + bombDamage)
	; the small volcanoes, one after another
	Float waited = 0.0
	If ventForm && marker
		Bool rays = SKSE.GetPluginVersion("ZenProphecyRage") > 0
		Float climb = VentClimb
		If thePlayer.IsInInterior()
			climb = VentClimbIndoors
		EndIf
		Float turn = Utility.RandomFloat(0.0, 360.0)
		Int v = 0
		While v < ventCount
			Float a = turn + v * 360.0 / ventCount + Utility.RandomFloat(-spread, spread)
			Float d = Utility.RandomFloat(ventNearest, ventFurthest)
			Float vx = gx + d * Math.Sin(a)
			Float vy = gy + d * Math.Cos(a)
			Float vz = gz
			ObjectReference mark = at.PlaceAtMe(marker, 1, False, False)
			mark.SetPosition(vx, vy, gz)
			String found = "the volcano's height (no ZenProphecyRage.dll)"
			Bool ok = True
			If rays
				Float below = GroundUnder(mark, 48.0 + climb * d, down)
				If below <= NoGround()
					ok = False
					found = "no ground"
				ElseIf below < gz - 48.0 - drop * d
					ok = False
					found = "ground " + below + " is a drop"
				Else
					vz = below
					found = "ground"
				EndIf
			EndIf
			If ok
				mark.SetPosition(vx, vy, vz)
				mark.PlaceAtMe(ventForm)
			EndIf
			Debug.Trace("[ZP Caldera eruption] small volcano " + (v + 1) + " at " + d + " units, z " + vz + " (" + found + ")" + PlacedNote(ok))
			mark.Delete()
			v += 1
			If v < ventCount
				Float gap = Utility.RandomFloat(gapMin, gapMax)
				Utility.Wait(gap)
				waited += gap
			EndIf
		EndWhile
	EndIf
	If soundFor > waited
		Utility.Wait(soundFor - waited)
	EndIf
	If lavaSound > 0
		Sound.StopInstance(lavaSound)
	EndIf
	If spot
		spot.Delete()
	EndIf
EndEvent

; The nearest living enemy within afReach of akPlayer and afArc degrees of its heading, or None.
Actor Function FoeInFront(Actor akPlayer, Float afReach, Float afArc) Global
	ObjectReference[] near = PO3_SKSEFunctions.FindAllReferencesOfFormType(akPlayer, 62, afReach)   ; 62 = Character
	Actor best = None
	Float bestDistance = afReach + 1.0
	Int i = 0
	While near && i < near.Length
		Actor other = near[i] as Actor
		If other && other != akPlayer && !other.IsDead() && other.IsHostileToActor(akPlayer)
			Float angle = akPlayer.GetHeadingAngle(other)
			If angle >= -afArc && angle <= afArc
				Float distance = akPlayer.GetDistance(other)
				If distance < bestDistance
					best = other
					bestDistance = distance
				EndIf
			EndIf
		EndIf
		i += 1
	EndWhile
	Return best
EndFunction

; The ground's height below akSpot (ZP_Aim.GroundBelow from afUp above it, afDown deep), or NoGround().
Float Function GroundUnder(ObjectReference akSpot, Float afUp, Float afDown) Global
	Float[] ground = ZP_Aim.GroundBelow(akSpot, afUp, afDown)
	If ground && ground.Length >= 1
		Return ground[0]
	EndIf
	Return NoGround()
EndFunction

Float Function NoGround() Global
	Return -1000000.0
EndFunction

String Function PlacedNote(Bool ok) Global
	If ok
		Return ""
	EndIf
	Return ": none placed"
EndFunction
