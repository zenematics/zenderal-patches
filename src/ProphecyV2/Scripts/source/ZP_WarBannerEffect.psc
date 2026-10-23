Scriptname ZP_WarBannerEffect extends ActiveMagicEffect
{Prophecy Glory - War Banner (lesser power, effect lasts 15 s). Sounds a war horn and plants a war standard in front
of the player: Enderal's camp banner frame (a bare pole and crossbar) with a Nehrimese banner hung from the crossbar,
turned to face the player. Once a
second, while the effect lasts: the player heals HealPerSecond if within Radius of the banner, and every hostile living
actor within Radius that is not already bound gets Triumvirate's Stave of Binding proc (immobilize + stamina drain,
chance to disarm, stagger). Triumvirate is read with GetFormFromFile, so without it the banner only heals.
The 5-minute cooldown is the Cooldown spell's effect on the player (Templar's pattern): while it lasts the power does
nothing but say so. Needs powerofthree's Papyrus Extender (FindAllReferencesOfFormType).}

Static Property Banner Auto
Form Property Cloth Auto            ; a MoveableStatic; Papyrus has no type for it
Sound Property HornSound Auto
Float Property ClothHeight = 390.0 Auto   ; the frame's crossbar (387-399 in CivilWarBanner02.nif)
Spell Property Cooldown Auto
MagicEffect Property CooldownEffect Auto
Float Property Radius = 400.0 Auto
Float Property HealPerSecond = 20.0 Auto
Float Property PlantDistance = 120.0 Auto

Int Property kActorCharacter = 62 AutoReadOnly

Actor player
ObjectReference flag
ObjectReference clothRef
Spell bind
MagicEffect bound
Bool finished

Event OnEffectStart(Actor akTarget, Actor akCaster)
	player = akCaster
	If player.HasMagicEffect(CooldownEffect)
		Debug.Notification("War Banner is not ready yet.")
		Dispel()
		Return
	EndIf
	Cooldown.Cast(player, player)
	HornSound.Play(player)
	; Placed from positioned XMarkers (PlaceAtMe takes the marker's position and rotation), so nothing is
	; moved or turned while disabled. 2026-10-22: the frame went missing in game while its cloth floated.
	Form xmarker = Game.GetForm(0x34)                      ; XMarker 000034:Skyrim.esm
	Float a = player.GetAngleZ()
	ObjectReference spot = player.PlaceAtMe(xmarker)
	spot.MoveTo(player, PlantDistance * Math.Sin(a), PlantDistance * Math.Cos(a), 0.0, False)
	spot.SetAngle(0.0, 0.0, a + 90.0)     ; the crossbar runs along the mesh's Y: turn it across the player's view
	ObjectReference top = spot.PlaceAtMe(xmarker)
	top.MoveTo(spot, 0.0, 0.0, ClothHeight, True)
	flag = spot.PlaceAtMe(Banner)
	clothRef = top.PlaceAtMe(Cloth)
	spot.Delete()
	top.Delete()
	Debug.Trace("[ZP WarBanner] placed frame " + flag + " at " + flag.GetPositionZ() + ", cloth " + clothRef + " at " + clothRef.GetPositionZ())
	If finished                           ; the effect ended while this was still placing: don't leave anything behind
		Debug.Trace("[ZP WarBanner] effect ended during setup - cleaning up")
		Cleanup()
		Return
	EndIf
	bind = Game.GetFormFromFile(0x423DA8, "Triumvirate - Mage Archetypes.esp") as Spell      ; TVR_Shaman_Spell_StaveBinding_Proc
	bound = Game.GetFormFromFile(0x423DA7, "Triumvirate - Mage Archetypes.esp") as MagicEffect ; its Immobilize effect
	Debug.Trace("[ZP WarBanner] bind spell " + bind + ", bound effect " + bound)
	RegisterForSingleUpdate(0.1)
EndEvent

Event OnUpdate()
	If !flag || finished
		Return
	EndIf
	If player.GetDistance(flag) <= Radius
		player.RestoreActorValue("Health", HealPerSecond)
	EndIf
	If bind
		ObjectReference[] near = PO3_SKSEFunctions.FindAllReferencesOfFormType(flag, kActorCharacter, Radius)
		Int found = 0
		Int cast = 0
		Int i = 0
		While near && i < near.Length
			Actor a = near[i] as Actor
			If a && a != player && !a.IsDead()
				found += 1
				If a.IsHostileToActor(player) && !a.HasMagicEffect(bound)
					bind.RemoteCast(player, player, a)
					cast += 1
				EndIf
			EndIf
			i += 1
		EndWhile
		Debug.Trace("[ZP WarBanner] update: " + found + " living actors in range, bound " + cast)
	EndIf
	RegisterForSingleUpdate(1.0)
EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	finished = True
	UnregisterForUpdate()
	Debug.Trace("[ZP WarBanner] effect finished")
	Cleanup()
EndEvent

Function Cleanup()
	If clothRef
		clothRef.Disable(True)
		clothRef.Delete()
		clothRef = None
	EndIf
	If flag
		flag.Disable(True)
		flag.Delete()
		flag = None
	EndIf
EndFunction
