Scriptname ZP_WhisperCleaveScript extends ActiveMagicEffect
{Whisper (Zenderal): Soul Cleave, the release (curator 2026-11-15, on Reaping Souls' orbs: "the effect when power attacking
is very underwelming, can we have a horizonal purple slash the fires out in a conal wave infront of us dealing magic
damage?"; then "make the the power attack not require a hit to trigger the wave"; then "make the projectile from the
power attack fire where the player is aiming rather than always just horizontal to the player" and the curator's poof
"on trigger"). Soul Rend came first (it fired, but its soul streams were too faint to see), then Reaping Souls.
Release() is Global and does the work; two callers:
- the swing (the main path): ZP_WhisperSoulsScript hears every weapon swing of the player's (SKSE's actor action 0)
  and, when the swing is Whisper's, Souls is full and the player is power attacking (powerofthree's IsPowerAttacking),
  calls Release with no struck enemy;
- this effect (a fallback): Whisper's enchantment starts it on the enemy a power attack hits while Souls is full (its
  conditions), for a power attack whose swing the game never reported. The swing comes first, so normally the souls
  are already spent when it runs and it does nothing.
Release:
- It claims the souls (GlobalVariable.Mod, thread-safe: a second release finds none), puts the glow out
  (ZP_WhisperSoulsScript.Show), plays the curator's poof and the soul trap's capture sound and the soul trap stream
  round the player.
- The aim: the crosshair's ray, from ZP_Aim.CameraAim() (the render camera's position and forward axis, a native in
  ZenProphecyRage.dll: Papyrus has no camera, and in third person TDM turns the body away from the crosshair). The
  wave starts on that ray, 120 units past the point of it abreast of the player's chest, and flies along it: where
  the crosshair points, up or down, in both views. Without the DLL (no answer) it aims along the player's own look
  angles from the chest instead (right in first person).
- The wave: Wave (Soul Cleave: magic damage to every actor its cone passes through, and the wisp's mark; its
  projectile, Fire Breath's wave record shape, carries tools/05's purple crescent) RemoteCast, blamed on the player,
  from an empty activator at the start, at one 1500 further along the aim. The start is 120 or more from the player's
  chest, clear of every player magic node by more than RemoteCastAimFix's 64, so Hit Where You Aim leaves its aim
  alone (Argent Verdict's orbs launch the same way).
- Inside where the wave begins: every living actor hostile to the player within 120 of the player and 70 degrees of
  the aim's heading (and the struck enemy, if any, within 120) takes Wave directly (DoCombatSpellApply).
- The markers are deleted 1.5 s later (a projectile needs them only at launch). Each release writes a line to the
  Papyrus log ([ZP Whisper release]) with the aim and where it came from.
Needs powerofthree's Papyrus Extender.}

Spell Property Wave Auto
Activator Property EmptyActivator Auto      ; vanilla FXEmptyActivator 0B79FF
GlobalVariable Property Souls Auto
Sound Property ReleaseSound Auto            ; vanilla MAGMysticismSoulTrapCapture 056AC6
Sound Property PoofSound Auto               ; ZP_WhisperPoofSound 823: the curator's 02. Cartoon Poof SFX
VisualEffect Property GatherVFX Auto        ; vanilla SoulTrapPVFX02 0531B1: round the player
Actor Property PlayerRef Auto

Int Property Full = 5 AutoReadOnly          ; 03-build-records.py SOULS (checked)

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Actor thePlayer = PlayerRef
	If !akTarget || !thePlayer || akTarget == thePlayer || akCaster != thePlayer
		Return
	EndIf
	Release(thePlayer, akTarget, Wave, EmptyActivator, Souls, Full, ReleaseSound, PoofSound, GatherVFX, "the hit")
EndEvent

Function Release(Actor akPlayer, Actor akStruck, Spell akWave, Activator akMarker, GlobalVariable akSouls, Int aiFull, Sound akSound, Sound akPoof, VisualEffect akGather, String asBy) Global
	Float ahead = 120.0       ; the wave starts this far past the player (more than 64 from its magic nodes: RemoteCastAimFix)
	Float chest = 95.0        ; above the player's feet
	Float far = 1500.0        ; the aim point past the start (beyond the wave's range)
	Float arc = 70.0          ; degrees either side of the aim's heading: the direct blows inside where the wave begins
	If !akPlayer || !akWave || !akMarker || !akSouls
		Return
	EndIf
	; claim the souls
	If akSouls.Mod(-aiFull as Float) < 0.0
		akSouls.Mod(aiFull as Float)             ; another release took them
		Return
	EndIf
	ZP_WhisperSoulsScript.Show(akPlayer, 0, aiFull)
	If akPoof
		akPoof.Play(akPlayer)
	EndIf
	If akSound
		akSound.Play(akPlayer)
	EndIf
	If akGather
		akGather.Play(akPlayer, 1.0)
	EndIf
	; the aim: the crosshair's ray (the camera), else the player's look angles from the chest
	Float cx = akPlayer.GetPositionX()
	Float cy = akPlayer.GetPositionY()
	Float cz = akPlayer.GetPositionZ() + chest
	Float dx
	Float dy
	Float dz
	Float sx
	Float sy
	Float sz
	String source = "the camera"
	Float[] aim = ZP_Aim.CameraAim()
	If aim && aim.Length == 6
		dx = aim[3]
		dy = aim[4]
		dz = aim[5]
		Float along = (cx - aim[0]) * dx + (cy - aim[1]) * dy + (cz - aim[2]) * dz + ahead   ; abreast of the chest, then ahead
		sx = aim[0] + along * dx
		sy = aim[1] + along * dy
		sz = aim[2] + along * dz
	Else
		source = "the player's angles (no ZenProphecyRage.dll aim)"
		Float pitch = akPlayer.GetAngleX()       ; positive looks down
		Float heading = akPlayer.GetAngleZ()
		dx = Math.Sin(heading) * Math.Cos(pitch)
		dy = Math.Cos(heading) * Math.Cos(pitch)
		dz = -Math.Sin(pitch)
		sx = cx + ahead * dx
		sy = cy + ahead * dy
		sz = cz + ahead * dz
	EndIf
	ObjectReference from = akPlayer.PlaceAtMe(akMarker, 1, False, False)
	from.SetPosition(sx, sy, sz)
	ObjectReference into = akPlayer.PlaceAtMe(akMarker, 1, False, False)
	into.SetPosition(sx + far * dx, sy + far * dy, sz + far * dz)
	akWave.RemoteCast(from, akPlayer, into)
	; inside where the wave begins
	Float hx = dx
	Float hy = dy
	Float hl = Math.Sqrt(hx * hx + hy * hy)
	Float cosArc = Math.Cos(arc)
	Int direct = 0
	ObjectReference[] near = PO3_SKSEFunctions.FindAllReferencesOfFormType(akPlayer, 62, ahead)
	Int i = 0
	While near && i < near.Length
		Actor a = near[i] as Actor
		If a && a != akPlayer && !a.IsDead() && a.IsHostileToActor(akPlayer) && akPlayer.GetDistance(a) < ahead
			Float vx = a.GetPositionX() - akPlayer.GetPositionX()
			Float vy = a.GetPositionY() - akPlayer.GetPositionY()
			Float vl = Math.Sqrt(vx * vx + vy * vy)
			Bool inFront = hl < 0.01 || vl < 1.0 || (vx * hx + vy * hy) / (vl * hl) > cosArc   ; straight up/down: all round
			If a == akStruck || inFront
				akPlayer.DoCombatSpellApply(akWave, a)
				direct += 1
			EndIf
		EndIf
		i += 1
	EndWhile
	Debug.Trace("[ZP Whisper release] souls claimed on " + asBy + "; the wave thrown along (" + dx + ", " + dy + ", " + dz + ") from " + source + ", " + direct + " enemies inside it hit directly")
	Utility.Wait(1.5)
	from.Delete()
	into.Delete()
EndFunction
