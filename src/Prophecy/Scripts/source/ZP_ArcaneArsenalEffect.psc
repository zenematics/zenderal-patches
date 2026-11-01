Scriptname ZP_ArcaneArsenalEffect extends ActiveMagicEffect
{Arcane Arsenal (Arcane Archery 1): the lesser power asks which element the player's arrows carry and stores it in
Element (0 none, 1 fire, 2 frost, 3 lightning). The gun hit spell's three contact-damage effects read the global.}

Message Property Menu Auto
GlobalVariable Property Element Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Int choice = Menu.Show()        ; Fire, Frost, Lightning, None
	If choice == 0
		Element.SetValue(1)
		Debug.Notification("Your arrows now carry fire.")
	ElseIf choice == 1
		Element.SetValue(2)
		Debug.Notification("Your arrows now carry frost.")
	ElseIf choice == 2
		Element.SetValue(3)
		Debug.Notification("Your arrows now carry lightning.")
	ElseIf choice == 3
		Element.SetValue(0)
		Debug.Notification("Your arrows carry no element.")
	EndIf
EndEvent
