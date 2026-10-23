Scriptname ZP_ProphecyNode extends ObjectReference
{A walk-up Prophecy star (v2 sanctum): the invisible collision box over each star, like Enderal's
_00E_Class_Acti_* nodes. Hands the activation to the sanctum quest, which owns the perk logic.}

Int Property Index Auto
ZP_ProphecySanctum Property Sanctum Auto

Event OnActivate(ObjectReference akActionRef)
	If akActionRef == Game.GetPlayer()
		Sanctum.ActivateNode(Index)
	EndIf
EndEvent
