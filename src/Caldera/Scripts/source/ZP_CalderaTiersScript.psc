Scriptname ZP_CalderaTiersScript extends ActiveMagicEffect
{Caldera (Zenderal): the head's lava cracks show the charge. The hammer's mesh carries five copies of its head, each
under a node ZP_CalderaTier0..4 (tools/01-build-mesh.py): tier t's glow map lights more of the cracks. Exactly one is
at scale 1 (SKSE NetImmerse.SetNodeScale, both views; Argent Verdict's knuckle motes work the same way): Tier(Charges)
of them, so the last tier lights only at a full charge. This ability (added while the hammer is equipped,
ZP_CalderaEquipScript; and by the first charge, for a hammer already in hand) sets them on start and again every Poll
seconds: a weapon's 3D is rebuilt with the file's scales (Tier0 lit) on every equip, load and race change. Show() and
Tier() are Global, so the charge and eruption scripts set them at once.
It also starts the eruption on the swing (curator 2026-11-16: "add a mana cost to the power attack trigger and make it
so you don't need to hit to trigger it"): every weapon swing of the player's is reported here (SKSE's actor action 0,
registered on this effect, again on every poll, so a hammer already in hand on an older save hears it too); a swing of
the hammer's (the source is Hammer) while Charges is full and the player is power attacking (powerofthree's
IsPowerAttacking) casts Eruption (ZP_CalderaEruptionSwing) on the player, hit or miss: the eruption script takes the
charges and the Mana, and finds where. Whisper's Soul Cleave hears its swing the same way.}

GlobalVariable Property Charges Auto
Weapon Property Hammer Auto                          ; Caldera 800
Spell Property Eruption Auto                         ; ZP_CalderaEruptionSwing 81B
Actor Property PlayerRef Auto
Float Property Poll = 1.0 AutoReadOnly
Int Property Tiers = 5 AutoReadOnly                  ; tools/01-build-mesh.py TIERS
Int Property Hits = 8 AutoReadOnly                   ; 02-build-records.py HITS

Event OnEffectStart(Actor akTarget, Actor akCaster)
	RegisterForActorAction(0)                        ; weapon swings: the eruption
	If Charges && akTarget
		Show(akTarget, Tier(Charges.GetValueInt(), Hits, Tiers), Tiers)
		RegisterForSingleUpdate(Poll)
	EndIf
EndEvent

Event OnUpdate()
	Actor holder = GetTargetActor()
	If Charges && holder
		RegisterForActorAction(0)                    ; (a set: once is kept once) for an effect started by an older build
		Show(holder, Tier(Charges.GetValueInt(), Hits, Tiers), Tiers)
		RegisterForSingleUpdate(Poll)
	EndIf
EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	UnregisterForActorAction(0)
EndEvent

; a power attack with the hammer at a full charge: the eruption at the swing, hit or miss
Event OnActorAction(Int actionType, Actor akActor, Form source, Int slot)
	Actor thePlayer = PlayerRef
	GlobalVariable count = Charges
	Spell release = Eruption
	If actionType != 0 || !thePlayer || akActor != thePlayer || !count || !release || !Hammer || source != Hammer
		Return
	EndIf
	If count.GetValueInt() < Hits || !PO3_SKSEFunctions.IsPowerAttacking(thePlayer)
		Return
	EndIf
	release.Cast(thePlayer, thePlayer)
EndEvent

; The tier aiCharges of aiFull charges light: whole steps only, so the top tier only at a full charge.
Int Function Tier(Int aiCharges, Int aiFull, Int aiTiers) Global
	If aiFull <= 0 || aiCharges <= 0
		Return 0
	EndIf
	If aiCharges >= aiFull
		Return aiTiers - 1
	EndIf
	Return aiCharges * (aiTiers - 1) / aiFull
EndFunction

; Tier aiTier at scale 1, the others at 0, in the third- and first-person 3D.
Function Show(Actor akActor, Int aiTier, Int aiTiers) Global
	Int i = 0
	While i < aiTiers
		Float s = 0.0
		If i == aiTier
			s = 1.0
		EndIf
		String node = "ZP_CalderaTier" + i
		NetImmerse.SetNodeScale(akActor, node, s, False)
		NetImmerse.SetNodeScale(akActor, node, s, True)
		i += 1
	EndWhile
EndFunction
