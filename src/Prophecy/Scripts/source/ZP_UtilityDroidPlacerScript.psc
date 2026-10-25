Scriptname ZP_UtilityDroidPlacerScript extends ObjectReference
{Prophecy Gadgets - Utility Droid, thrown (curator 2026-10-23). The thrown droid's landing explosion places this
invisible activator where it lands - SureAI's Starling Dummy talent chain (_00E_A2_StarlingdummyExp places
_00E_A2_StarlingdummyPlacer, whose _00E_A2_StarlingdummySC raises a dust burst, waits 0.3 s and places the spider).
Here it places the droid instead, right where it landed, sets its Health (BaseHealth + HealthPerLevel per player
level), makes it a teammate, remembers it in DroidList, and removes itself. No navmesh snap, as SureAI's has none: the
first build called PO3's MoveToNearestNavmeshLocation, which moves to the nearest navmesh VERTEX (its symbols iterate
BSNavmeshVertex), meters off the landing spot on open ground (curator 2026-10-23: "placement ... vs the throw is off").}

ActorBase Property Droid Auto
FormList Property DroidList Auto
Explosion Property DustExplosion Auto      ; _00E_FXDustExplosion
Float Property BaseHealth = 100.0 Auto
Float Property HealthPerLevel = 10.0 Auto

Event OnInit()
	Actor player = Game.GetPlayer()
	PlaceAtMe(DustExplosion)
	Utility.Wait(0.3)
	Actor d = PlaceActorAtMe(Droid)
	If d
		d.SetAngle(0.0, 0.0, player.GetAngleZ())
		d.SetActorValue("Health", BaseHealth + HealthPerLevel * player.GetLevel())
		d.RestoreActorValue("Health", 100000.0)
		d.SetPlayerTeammate(true)
		DroidList.Revert()
		DroidList.AddForm(d)
		Debug.Notification("Utility Droid deployed.")
	EndIf
	Disable()
	Delete()
EndEvent
