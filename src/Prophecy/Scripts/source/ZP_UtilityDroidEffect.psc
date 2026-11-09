Scriptname ZP_UtilityDroidEffect extends ActiveMagicEffect
{Prophecy Gadgets - Utility Droid's ability (on the droid). Once a second it counts up two timers:
  - every HealInterval seconds, if the player is within HealRadius and hurt, it restores HealAmount Health to them;
  - every StaggerInterval seconds, while the droid is in combat, it casts StaggerSpell on each living actor hostile to
    the player within StaggerRadius of the droid (powerofthree's Papyrus Extender FindAllReferencesOfFormType, as
    Seismic Stomp does).
One droid at a time, from the droid's side (2026-11-05, curator: the fix must reach existing saves): every tick the
droid checks DroidList (0x946, looked up by ID - no property reaches a running effect). If the list names another
living droid, this one is a duplicate and removes itself (Disable + Delete); if it names none, this one claims the
list. Two droids that both claim converge: the later claim wins, the other sees it next tick. Runs wherever the droid
is, so a save that already holds two or more is cleaned the moment they tick, whatever cell they are in.
  - every ScavengeInterval seconds, out of combat and within HealRadius of the player, it has a ScavengeChance % roll
    to find ScavengeCount Spare Parts for them, at most once every ScavengeHours game hours (curator 2026-11-05:
    "find spare parts ... random but limited to only 1 per 3 hours"; SpareParts looked up by ID on a droid that
    predates the property; the last find is kept as a game-time day in the save).
Existing saves (curator 2026-11-05): a droid placed before a property existed has it at 0 / None in its running
effect (only the record's values at the first apply reach an instance), so Defaults() fills every tunable that reads
as unset with the shipped number, each tick - the scavenging and the one-droid check then work on old droids too.
Stops when the droid dies.}

Spell Property StaggerSpell Auto
Spell Property HealSpell Auto              ; ZP_Prophecy_UtilityDroid_Heal: HealAmount through Enderal's heal-other effect, for its look
Float Property HealAmount = 15.0 Auto
Int Property HealInterval = 4 Auto
Float Property HealRadius = 640.0 Auto
Int Property StaggerInterval = 6 Auto
Float Property StaggerRadius = 300.0 Auto
MiscObject Property SpareParts Auto        ; _00E_CraftingPieces 0773ED
Int Property ScavengeInterval = 60 Auto      ; seconds between rolls
Float Property ScavengeChance = 15.0 Auto     ; % per roll
Float Property ScavengeHours = 3.0 Auto       ; game hours between finds, at least
Int Property ScavengeCount = 1 Auto

Int Property kActorCharacter = 62 AutoReadOnly

Actor me
Int healTick
Int staggerTick
Int scavengeTick
Float lastFindDay = -1000.0   ; game time (days) of the last find
FormList droidList      ; ZP_Prophecy_UtilityDroid_Current, looked up by ID (see the top)

Event OnEffectStart(Actor akTarget, Actor akCaster)
	me = akTarget
	RegisterForSingleUpdate(1.0)
EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	me = None
EndEvent

Event OnUpdate()
	If !me || me.IsDead()
		Return
	EndIf
	Defaults()
	If IsDuplicate()
		Debug.Trace("ZP_UtilityDroidEffect: duplicate droid " + me + " removed; keeping " + droidList.GetAt(0))
		me.Disable()
		me.Delete()
		me = None
		Return
	EndIf
	Actor player = Game.GetPlayer()
	healTick += 1
	If healTick >= HealInterval
		healTick = 0
		If me.GetDistance(player) <= HealRadius && player.GetActorValuePercentage("Health") < 1.0
			Heal(player)
		EndIf
	EndIf
	scavengeTick += 1
	If scavengeTick >= ScavengeInterval
		scavengeTick = 0
		If !me.IsInCombat() && me.GetDistance(player) <= HealRadius && (Utility.GetCurrentGameTime() - lastFindDay) * 24.0 >= ScavengeHours
			If Utility.RandomFloat(0.0, 100.0) < ScavengeChance
				Scavenge(player)
			EndIf
		EndIf
	EndIf
	staggerTick += 1
	If staggerTick >= StaggerInterval && me.IsInCombat()
		staggerTick = 0
		ObjectReference[] near = PO3_SKSEFunctions.FindAllReferencesOfFormType(me, kActorCharacter, StaggerRadius)
		Int i = 0
		While near && i < near.Length
			Actor a = near[i] as Actor
			If a && a != me && a != player && !a.IsDead() && a.IsHostileToActor(player)
				StaggerSpell.Cast(me, a)
			EndIf
			i += 1
		EndWhile
	EndIf
	RegisterForSingleUpdate(1.0)
EndEvent

; the shipped values for anything a pre-property droid's effect holds as unset (0 / None / 0.0)
Function Defaults()
	If HealInterval <= 0
		HealInterval = 4
	EndIf
	If HealRadius <= 0.0
		HealRadius = 640.0
	EndIf
	If HealAmount <= 0.0
		HealAmount = 15.0
	EndIf
	If StaggerInterval <= 0
		StaggerInterval = 6
	EndIf
	If StaggerRadius <= 0.0
		StaggerRadius = 300.0
	EndIf
	If ScavengeInterval <= 0
		ScavengeInterval = 60
	EndIf
	If ScavengeChance <= 0.0
		ScavengeChance = 15.0
	EndIf
	If ScavengeHours <= 0.0
		ScavengeHours = 3.0
	EndIf
	If ScavengeCount < 1
		ScavengeCount = 1
	EndIf
	If !SpareParts
		SpareParts = Game.GetFormFromFile(0x0773ED, "Skyrim.esm") as MiscObject
	EndIf
	If !StaggerSpell
		StaggerSpell = Game.GetFormFromFile(0x000943, "Zenderal - Prophecy.esp") as Spell
	EndIf
EndFunction

; True when DroidList names another living droid (this one must go); claims the list when it names none.
Bool Function IsDuplicate()
	If !droidList
		droidList = Game.GetFormFromFile(0x000946, "Zenderal - Prophecy.esp") as FormList
		If !droidList
			Return False
		EndIf
	EndIf
	Actor keeper = None
	If droidList.GetSize() > 0
		keeper = droidList.GetAt(0) as Actor
	EndIf
	If keeper == me
		Return False
	EndIf
	If keeper && !keeper.IsDead() && !keeper.IsDisabled()
		Return True
	EndIf
	droidList.Revert()
	droidList.AddForm(me)
	Return False
EndFunction

Function Scavenge(Actor akPlayer)
	If !SpareParts
		SpareParts = Game.GetFormFromFile(0x0773ED, "Skyrim.esm") as MiscObject
	EndIf
	If !SpareParts || ScavengeCount < 1
		Return
	EndIf
	lastFindDay = Utility.GetCurrentGameTime()
	akPlayer.AddItem(SpareParts, ScavengeCount, true)
	If ScavengeCount == 1
		Debug.Notification("Your Utility Droid found a Spare Part.")
	Else
		Debug.Notification("Your Utility Droid found " + ScavengeCount + " Spare Parts.")
	EndIf
EndFunction

Function Heal(Actor akPlayer)
	; the heal is a spell cast at the player (curator 2026-10-23: "an effect for when the droid heals me"): Enderal's
	; RestoreHealthFFActor shows its healing shimmer on them. A droid already out when this shipped has no HealSpell
	; (a property added to a running effect stays None in the save), so it is looked up, and the bare heal is the fallback.
	If !HealSpell
		HealSpell = Game.GetFormFromFile(0x0009AF, "Zenderal - Prophecy.esp") as Spell
	EndIf
	If HealSpell
		HealSpell.RemoteCast(me, me, akPlayer)
	Else
		akPlayer.RestoreActorValue("Health", HealAmount)
	EndIf
EndFunction
