Scriptname ZP_RighteousPathWard extends ActiveMagicEffect
{Prophecy Faith - Righteous Path's visible ward (2026-10-25). On the ability's effect that is condition-gated on
IsBlocking + a left hand that is empty or holds a spell, so the engine starts it however the block began: Dual Wield
Parrying forces its block by sending blockStart into the graph and setting IsBlocking, which raises none of the
block events ZP_RighteousPathEffect listens for. Starts: wear WardShield (Kittytails' shield of light, FX01 slot).
Ends: take it off. ZP_RighteousPathEffect does the same on a normal block's events, sooner; both are idempotent.}

Armor Property WardShield Auto

; ZenProphecyUI.dll (Prophecy v3) shows and hides the ward itself, at once; this path is v1's
Bool Function DllWard()
	Return SKSE.GetPluginVersion("ZenProphecyUI") > 0
EndFunction

Event OnEffectStart(Actor akTarget, Actor akCaster)
	If !WardShield || !akTarget || DllWard()
		Return
	EndIf
	If akTarget.GetItemCount(WardShield) < 1
		akTarget.AddItem(WardShield, 1, True)
	EndIf
	If !akTarget.IsEquipped(WardShield)
		akTarget.EquipItem(WardShield, True, True)
	EndIf
EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	If WardShield && akTarget && !DllWard() && akTarget.GetItemCount(WardShield) > 0
		akTarget.UnequipItem(WardShield, True, True)
		akTarget.RemoveItem(WardShield, akTarget.GetItemCount(WardShield), True)
	EndIf
EndEvent
