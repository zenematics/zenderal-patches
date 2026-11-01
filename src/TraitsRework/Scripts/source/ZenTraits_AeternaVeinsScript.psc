Scriptname ZenTraits_AeternaVeinsScript extends activemagiceffect
{Zen Traits' Aeterna Veins (shazdeh, MIT), forked by Zenderal - Traits (curator 2026-10-25: the -20% max Health cut
follows every change to max Health, and no full heal). Shipped loose in Zenderal - Traits, which outranks Zenderal -
Patch Collection (Zen Traits' copy) in MO2.
Upstream added DebuffSpell (a Health debuff sized by its perk's ModSpellMagnitude MultiplyAVMult Health 0.2 entry,
which reads Health as it is, hence its RestoreAV 10000 first) and re-added it on PO3's OnLevelIncrease only. Now the
cut is Zenderal - Traits' ZEN_TR_AeternaVeinsPenaltyAb (0x86F), kept at 20% of the uncut maximum (SKSE's
GetActorValueMax + the cut already applied) every 5 s, as ZEN_TR_PoolPenaltyEffect does for Zenderal's traits:
level-ups, gear, potions and buffs all count, and re-adding a Recover modifier never heals. Upstream's debuff is no
longer added, and is removed from saves that have it (on effect start, and on load for saves made with upstream's
script). Properties unchanged: a script-only replacement must keep them; the new ability is found by FormID.}

Import PO3_Events_AME

Spell Property DebuffSpell Auto
Actor Property PlayerRef Auto

Spell penalty
Float applied
Bool finished

Event OnEffectStart(Actor akTarget, Actor akCaster)
    Begin()
EndEvent

; saves made with upstream's script: drop its debuff and start the live cut
Event OnPlayerLoadGame()
    Begin()
EndEvent

; upstream's level-up registration, still live in older saves
Event OnLevelIncrease(int aiLevel)
    Refresh()
EndEvent

Event OnUpdate()
    If finished
        Return
    EndIf
    Refresh()
    RegisterForSingleUpdate(5.0)
EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)
    finished = True
    PlayerRef.RemoveSpell(DebuffSpell)
    If penalty
        PlayerRef.RemoveSpell(penalty)
    EndIf
    UnregisterForLevelIncrease(Self)
EndEvent

Function Begin()
    If finished
        Return
    EndIf
    PlayerRef.RemoveSpell(DebuffSpell)
    UnregisterForLevelIncrease(Self)
    Refresh()
    RegisterForSingleUpdate(5.0)
EndFunction

Function Refresh()
    If !penalty
        penalty = Game.GetFormFromFile(0x00086F, "Zenderal - Traits.esp") as Spell
        If !penalty
            Return
        EndIf
    EndIf
    Float uncut = PlayerRef.GetActorValueMax("Health") + applied
    Float want = Math.Floor(uncut * 0.2 + 0.5)
    If Math.Abs(want - applied) < 1.0
        Return
    EndIf
    PlayerRef.RemoveSpell(penalty)
    penalty.SetNthEffectMagnitude(0, want)
    PlayerRef.AddSpell(penalty, False)
    applied = want
EndFunction
