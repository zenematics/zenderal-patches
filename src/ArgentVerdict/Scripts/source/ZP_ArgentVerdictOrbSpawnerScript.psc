Scriptname ZP_ArgentVerdictOrbSpawnerScript extends ObjectReference
{Argent Verdict (Zenderal): a smite beam's orbs (curator 2026-11-14: "can we add the motes we use on the knuckles as
orbs that fire out of the smite beams (just like the regular Smith from Prophecy talent but dark heirophant effect)",
then "I want this but the Dark heirophant effects / colors"). On the orb spawner activator (ACTI 860), which the
beam's impact explosion (EXPL 857, placed at each smitten enemy's feet as its beam strikes) places as its
PlacedObject: Prophecy's own Smite works this way (its explosion A54 places activator A46, whose script
_LIP_LightshaftSkyboltActivatorScript fires the light shafts from OnInit), and the curator sees those in game.
OnInit: Orbs orbs (Orb: Prophecy's Smite orb in white and black) fly out, each RemoteCast, blamed on the player, from
an empty activator StartOut units out from the spawner at OrbHeight, at one OrbRange further out the same way, in
directions spread evenly round the circle from a random start (plus or minus Jitter degrees), between AimLow below and
AimHigh above the launch height. The heights are Prophecy's (A46's SpawnHeight 80, MaxLow 50, MaxHeight 80, read
from its bytecode). Each burst writes a line to the Papyrus log ([ZP Argent orbs]). The markers and the spawner are
deleted MarkerLife s later (a projectile needs its markers only at launch).
Before this the beam itself fired them: first from OnLoad (the orbs started inside the enemy: "no orbs appear"), then
from OnActivate when the release activated it ("it doesn't seem the orbs appear at all"; the Papyrus log of that
test has no line from it at all). The next three builds' orbs flew along the floor ("almost under the floor", "still
on the floor", "still seems to fire the orbs low") whatever OrbHeight said: their position locals were named x, y and
z, and inside the loop the compiler read those names as this reference's own X, Y and Z properties
(ObjectReference.psc), so every marker sat at the spawner's own height, the enemy's feet (the bytecode has
"propget z, self" there). Never name a local x, y or z in a script that extends ObjectReference.}

Spell Property Orb Auto
Activator Property EmptyActivator Auto
Actor Property PlayerRef Auto

Int Property Orbs = 4 AutoReadOnly                   ; 02-build-records.py ORBS (the item card)
Float Property StartOut = 90.0 AutoReadOnly          ; clear of the enemy under the beam (a giant's body is wider)
Float Property OrbHeight = 80.0 AutoReadOnly         ; above the enemy's feet: Prophecy's SpawnHeight
Float Property OrbRange = 700.0 AutoReadOnly         ; how far beyond StartOut each orb is aimed
Float Property Jitter = 20.0 AutoReadOnly
Float Property AimLow = 50.0 AutoReadOnly            ; the aim point, below the launch height: Prophecy's MaxLow
Float Property AimHigh = 80.0 AutoReadOnly           ; and above it: Prophecy's MaxHeight
Float Property MarkerLife = 1.0 AutoReadOnly

Event OnInit()
	Spell orbSpell = Orb
	Activator markerBase = EmptyActivator
	Actor thePlayer = PlayerRef
	Int count = Orbs
	Float out = StartOut
	Float height = OrbHeight
	Float reach = OrbRange
	Float jit = Jitter
	Float low = AimLow
	Float high = AimHigh
	Float life = MarkerLife
	If !orbSpell || !markerBase || !thePlayer
		Debug.Trace("[ZP Argent orbs] not fired: orb " + orbSpell + ", marker " + markerBase + ", player " + thePlayer)
		Return
	EndIf
	Float baseX = GetPositionX()
	Float baseY = GetPositionY()
	Float baseZ = GetPositionZ()
	Float launchZ = baseZ + height
	ObjectReference[] marks = new ObjectReference[16]
	Float start = Utility.RandomFloat(0.0, 360.0)
	Int i = 0
	While i < count && 2 * i + 1 < marks.Length
		Float a = start + 360.0 * i / count + Utility.RandomFloat(-jit, jit)
		Float dx = Math.Cos(a)
		Float dy = Math.Sin(a)
		ObjectReference from = PlaceAtMe(markerBase, 1, False, False)
		from.SetPosition(baseX + out * dx, baseY + out * dy, launchZ)
		ObjectReference into = PlaceAtMe(markerBase, 1, False, False)
		into.SetPosition(baseX + (out + reach) * dx, baseY + (out + reach) * dy, launchZ + Utility.RandomFloat(-low, high))
		orbSpell.RemoteCast(from, thePlayer, into)
		marks[2 * i] = from
		marks[2 * i + 1] = into
		i += 1
	EndWhile
	Debug.Trace("[ZP Argent orbs] " + i + " orbs from " + baseX + ", " + baseY + ", " + launchZ + " (spawner at " + baseZ + ", first marker at " + marks[0].GetPositionZ() + ")")
	Utility.Wait(life)
	i = 0
	While i < marks.Length
		If marks[i]
			marks[i].Delete()
		EndIf
		i += 1
	EndWhile
	Disable()
	Delete()
EndEvent
