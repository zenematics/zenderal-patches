Scriptname ZP_ClockworkThunderSale extends TopicInfo Hidden
{Clockwork Thunder (Zenderal): buying the rifle from Yerai (response 0x812, "Splendid, that's it!" / "Again: Thank you.").
Runs when his line ends: takes Price gold and makes the rifle on his desk the player's, so taking it is not theft.
The response only shows while the player carries Price gold, the rifle still lies in the workshop and Sold is 0.}

MiscObject Property Gold Auto                 ; Gold001
ObjectReference Property Rifle Auto           ; the rifle on the desk (persistent ref 0x806)
GlobalVariable Property Sold Auto             ; ZP_ClockworkThunderSold
Int Property Price = 2000 AutoReadOnly

Function Fragment_0(ObjectReference akSpeakerRef)
	Actor buyer = Game.GetPlayer()
	If Sold.GetValue() != 0 || buyer.GetItemCount(Gold) < Price
		Return
	EndIf
	buyer.RemoveItem(Gold, Price)
	Rifle.SetActorOwner(buyer.GetActorBase())
	Sold.SetValue(1)
EndFunction
