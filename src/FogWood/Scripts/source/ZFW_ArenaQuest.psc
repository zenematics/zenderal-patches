Scriptname ZFW_ArenaQuest extends Quest
{Zenderal - Fog Wood: the endless-waves arena (curator's design, 2026-11-05).
 Enter from the Fogbound Stone in Whisperwood (placed by this script, so no Vyn cell is edited). Each wave is a
 horde of ONE kind of creature (a theme: regulars, elites, bosses, a shown name, a pack-size scale), drawn from
 the tier for the wave number; the next wave starts once the last is dead. Fixed ladder: tiers by wave number,
 more elites as the waves go, a boss every BOSS_EVERY waves.
 No rewards: the player leaves EPFaction for the run (Enderal's _00E_EPOnDeath pays kill EP only to a killer
 in it) and every corpse is stripped - then DROPS ON THE GROUND, beside it, ammo of the kind the player uses
 (equipped ammo through Papyrus Extender; the Flintlock Overhaul's bullets when a pistol is carried), elites
 and bosses health potions, Ambrosia and mana potions of the wave's tier. Practice death: the player is
 essential for the run; bleedout ends it and sends them back to the stone (ZFW_PlayerAlias, and the 1 s loop
 as the fallback). Timing uses real seconds, so the timescale does not matter.
 Every spawn is in one faction (Ally to itself), ignores friendly hits, fills one of 40 spawn aliases
 (ZFW_SpawnAlias reports hits from other spawns for the Papyrus log) and is pulled back onto the player every
 second: never idle, never searching, never fighting anything else.}

Actor Property PlayerRef Auto
Faction Property EPFaction Auto
{Enderal's EPFaction 039DCE: a killer outside it earns no EP from _00E_EPOnDeath.}
Faction Property ArenaFaction Auto
Activator Property FogStone Auto
ObjectReference Property StoneAnchor Auto
{Fallback anchor only (the first build's Grimlight Gallery marker, whatever a save holds). The spot itself is the
 STONE_* constants below: quest script PROPERTY values live in the save, so a rebuilt plugin cannot move the stone
 through them (2026-11-06: the move ran and put the stone back on the saved Whisperwood coordinates).}
ObjectReference Property EntryMarker Auto
ObjectReference[] Property SpawnMarkers Auto
WorldSpace Property FogWoodWorld Auto
FormList Property Tier1 Auto
{Each tier is a FormList of THEMES; a theme is a FormList: [0] regulars, [1] elites, [2] bosses, [3] a Message
 whose name is shown, [4] a GlobalVariable scaling the pack size.}
FormList Property Tier2 Auto
FormList Property Tier3 Auto
FormList Property Tier4 Auto
FormList Property Tier5 Auto
FormList Property HealthPotions Auto
{Enderal's Health Potions Cheap / Standard / Quality / Exclusive: index = PotionTier().}
FormList Property ManaPotions Auto
Potion Property Ambrosia Auto
GlobalVariable Property BestWave Auto
GlobalVariable Property CurrentWave Auto
GlobalVariable Property WaveSize Auto
{The current wave's pack size, for the objective text (<Global=ZFW_WaveSize>).}
FormList Property Themes Auto
ObjectReference[] Property CacheMarkers Auto
{40 XMarkers tools/01 put on clear lattice vertices (no tree within a vertex): the chests stand on these. The
 first build snapped random spots to the nearest navmesh vertex, and the lattice keeps the trunk vertices, so a
 chest stood inside a tree.}
Container Property ChestBase Auto
{ZFW_Chest, the Fogbound Cache: an empty small chest the script places and stocks (curator, 2026-11-06).}
FormList Property CachePotions Auto
{Enderal's Protection from Fire / Frost / Shock / Magic potions, every tier it ships.}
Potion Property StaminaPotion Auto
{Every theme in tools/02 order: a theme's index picks its objective (OBJ_WAVE0 + index, OBJ_BOSS0 + index).}
GlobalVariable Property QuestVersion Auto
{The quest's data version a save was last restarted at. A quest instance captures its text-display globals when
 it STARTS, so a save whose quest started before the banners existed never replaces <Global=...>: the Fogbound
 Stone restarts the quest once when this is below QUEST_VERSION (ZFW_StoneScript, outside the quest).}
FormList Property Persist Auto
{What survives that restart: [0] the placed Fogbound Stone.}
Message Property EnterMsg Auto
Message Property LeaveMsg Auto

Int Property BOSS_EVERY = 5 AutoReadOnly
Int Property MAX_SPAWNS = 30 AutoReadOnly
{Hordes (curator, 2026-11-05: "20+"): wave 1 fields FIRST_WAVE, each wave WAVE_STEP more, capped here (the
 arrays and the spawn aliases hold SLOTS). This many live actors with the list's physics, dismemberment and
 equipment-display plugins is untested; the Whisperwood hordes of 8-14 crashed twice on Mihail skeletons.}
Int Property SLOTS = 40 AutoReadOnly
Int Property FIRST_WAVE = 20 AutoReadOnly
Int Property WAVE_STEP = 2 AutoReadOnly
Int Property MIN_PACK = 6 AutoReadOnly
Int Property MAX_ELITES = 5 AutoReadOnly
{Elites per wave: 1 on wave 1, one more every ELITE_EVERY waves, up to MAX_ELITES. They count toward the cap.}
Int Property ELITE_EVERY = 3 AutoReadOnly
Int Property POTION_TIER_WAVES = 4 AutoReadOnly
{Potion quality climbs one tier every this many waves: Cheap 1-4, Standard 5-8, Quality 9-12, Exclusive 13+.}
Float Property SPREAD = 120.0 AutoReadOnly
Float Property FIRST_WAVE_DELAY = 10.0 AutoReadOnly
Float Property NEXT_WAVE_DELAY = 8.0 AutoReadOnly
Float Property AMMO_CHANCE = 0.7 AutoReadOnly
Float Property REGULAR_POTION_CHANCE = 0.1 AutoReadOnly
Float Property ELITE_HEALTH = 1.6 AutoReadOnly
Float Property BOSS_HEALTH = 2.5 AutoReadOnly
Float Property STONE_X = -72640.0 AutoReadOnly
{The Fogbound Stone's spot: cell (-18, 8) of the north-Heartland pine forest, between the Tower Encampment and
 Castle Bleakstar (tools/02 documents the choice). AutoReadOnly = baked into the .pex, so a recompile moves it.}
Float Property STONE_Y = 33856.0 AutoReadOnly
Float Property STONE_Z = 642.0 AutoReadOnly
Float Property STONE_ANGLE = 0.0 AutoReadOnly
Int Property STONE_ANCHOR_ID = 0x132F43 AutoReadOnly
{Tower Encampment map marker in Skyrim.esm (Enderal's), a persistent Vyn ref 5,143 units from the spot.}
Int Property QUEST_VERSION = 2 AutoReadOnly
{Bump to force one restart of the quest on existing saves (new objectives, text-display globals, properties).}
Int Property FRIEND_HITS = 100000 AutoReadOnly
{iFriendHitCombatAllowed / iFriendHitNonCombatAllowed for the run: the hits an ally may land before the victim turns
 on it (4 / 2). The hit log of 2026-11-06 showed bandits turning on bandits over their own spell projectiles.}
Int Property STUCK_SECONDS = 8 AutoReadOnly
{A live spawn that moves less than STUCK_MOVE units in this many seconds while the player is farther than
 STUCK_RANGE is logged (base, weapon, combat state, target) and teleported onto a spawn marker: a Vagrant stood
 still through a wave (curator, 2026-11-06), cause unknown until the log says.}
Float Property STUCK_MOVE = 48.0 AutoReadOnly
Float Property STUCK_RANGE = 400.0 AutoReadOnly
Float Property FAR_RANGE = 1800.0 AutoReadOnly
{Converge (curator, 2026-11-06: enemies got lost in the wood, stood in the distance doing nothing, the last one
 could not be found): a live spawn farther than this from the player for FAR_SECONDS is moved to the clear
 marker nearest the player, at least NEAR_MIN away, and restarted on them. The fog shows 2,500 units.}
Int Property FAR_SECONDS = 5 AutoReadOnly
Float Property NEAR_MIN = 500.0 AutoReadOnly
Float Property TICK_TIMEOUT = 30.0 AutoReadOnly
{A tick that has not finished in this long died of an error (its InTick flag never cleared): the next one runs.}
Int Property LAST_FEW = 3 AutoReadOnly
{Gather (tester report, 2026-11-07: a wave's last enemies could not be found, so the next wave never came): with
 this many or fewer alive and no kill for NO_KILL_SECONDS, every live spawn farther than NO_KILL_RANGE from the
 player is brought to the clear marker nearest the player. Nearer ones are left alone: a long boss fight is not a
 lost enemy.}
Float Property NO_KILL_SECONDS = 20.0 AutoReadOnly
Float Property NO_KILL_RANGE = 600.0 AutoReadOnly
Float Property BOUND = 11500.0 AutoReadOnly
{The wood is 6x6 cells round the origin with walls 512 inside the edge; a player past this on either axis is put
 back at the entry (the curator ran off the edge of the map: the invisible walls did not hold).}
Int Property STONE_VERSION = 3 AutoReadOnly
{Bump when STONE_X/Y/Z move: a save's already placed stone is moved to the new spot on the next load.
 1 = Whisperwood (-83776, 16832, 4452); 2 = pine forest through saved properties (never moved); 3 = constants.}
Int Property TRACE_BUDGET = 120 AutoReadOnly
{Papyrus-log lines a run may write about spawns hitting or targeting each other.}
String Property FLINTLOCK = "Zenderal - Flintlock Overhaul.esp" AutoReadOnly
Int Property OBJ_CLEARED = 1 AutoReadOnly
{Quest objectives are the wave banner (curator: large, centred, like the quest prompts). Text replacement
 fills <Global=ZFW_CurrentWave>, <Global=ZFW_WaveSize> and, on boss waves, <Alias=ZFW_Spawn01> (the boss).}
Int Property OBJ_START = 2 AutoReadOnly
Int Property OBJ_WAVE0 = 10 AutoReadOnly
Int Property OBJ_BOSS0 = 50 AutoReadOnly
Int Property OBJ_CACHES = 3 AutoReadOnly
Int Property CHESTS_AT_START = 6 AutoReadOnly
{Fogbound Caches: this many at the start of a run, CHESTS_PER_BOSS more after every boss wave, up to the array.
 Each sits on the navmesh within CHEST_SPREAD of a random spawn marker or the entry.}
Int Property CHESTS_PER_BOSS = 3 AutoReadOnly

ObjectReference StoneRef
Int StonePlaced = 0
Bool Property Running = False Auto Hidden
Bool WaveActive = False
Int Wave = 0
Float NextWaveAt = 0.0
Float LastKillAt = 0.0
Bool InTick = False
Float TickStarted = 0.0
Int EPRank = 0
Actor[] Spawned
Bool[] SpawnedElite
Bool[] SpawnedBoss
Actor[] Corpses
Int CorpseCount = 0
Actor[] Doomed                                  ; disabled this tick, deleted on a later one (DeleteDoomed): a player's
Int DoomedCount = 0                             ; crash-2026-11-07-05-00-46.log is SkyrimSE.exe+0FDDB2D (a weapon re-hung on a
                                                ; freed 3D root) on an arena skeleton this script had just Disable()d + Delete()d
                                                ; in one frame; see arch-docs/patches/EnemyDensity.md, sixth postmortem
ObjectReference[] Drops
Int DropCount = 0
ObjectReference[] OldDrops
Int OldDropCount = 0
Bool Busy = False
FormList LastTheme
Int TraceBudget = 0
Int ShownObjective = -1
String EndNote = ""
ObjectReference[] Chests
Int ChestCount = 0
Bool[] CacheUsed
Float[] LastX
Float[] LastY
Int[] StillFor
Int[] FarFor
Int SavedFriendHits = -1
Int SavedFriendHitsNC = -1

Event OnInit()
	Spawned = new Actor[40]
	SpawnedElite = new Bool[40]
	SpawnedBoss = new Bool[40]
	Corpses = new Actor[80]
	Doomed = new Actor[120]
	Drops = new ObjectReference[128]
	OldDrops = new ObjectReference[128]
	Chests = new ObjectReference[32]
	LastX = new Float[40]
	LastY = new Float[40]
	StillFor = new Int[40]
	FarFor = new Int[40]
	RegisterForSingleUpdate(3.0)
EndEvent

ObjectReference Function Anchor()
	{The persistent Vyn ref the stone is placed at and moved through, by FormID (a saved property would be stale).}
	ObjectReference anchor = Game.GetFormFromFile(STONE_ANCHOR_ID, "Skyrim.esm") as ObjectReference
	If anchor == None
		anchor = StoneAnchor
	EndIf
	Return anchor
EndFunction

Function EnsureStone()
	{Places the Fogbound Stone once (persistent, so it survives cell resets and saves), and moves a stone a save
	 already holds when the spot changed (STONE_VERSION).}
	ObjectReference anchor = Anchor()
	If anchor == None || FogStone == None
		Return
	EndIf
	If StoneRef == None && Persist != None && Persist.GetSize() > 0
		StoneRef = Persist.GetAt(0) as ObjectReference     ; back from the quest restart
		StonePlaced = STONE_VERSION
	EndIf
	If StoneRef == None
		StoneRef = anchor.PlaceAtMe(FogStone, 1, True, True)
		StoneRef.SetPosition(STONE_X, STONE_Y, STONE_Z)
		StoneRef.SetAngle(0.0, 0.0, STONE_ANGLE)
		StoneRef.Enable()
		StonePlaced = STONE_VERSION
		Debug.Trace("ZFW: stone placed at " + STONE_X + ", " + STONE_Y + ", " + STONE_Z)
	ElseIf StonePlaced != STONE_VERSION
		StoneRef.MoveTo(anchor)                   ; into the new spot's cell first: SetPosition alone stays in the old one
		StoneRef.SetPosition(STONE_X, STONE_Y, STONE_Z)
		StoneRef.SetAngle(0.0, 0.0, STONE_ANGLE)
		StonePlaced = STONE_VERSION
		Debug.Trace("ZFW: stone moved to " + STONE_X + ", " + STONE_Y + ", " + STONE_Z + " (version " + STONE_VERSION + ")")
	EndIf
EndFunction

Function OnGameLoaded()
	{From the player alias, every load.}
	If !Spawned || !Drops || !Chests || (!Running && Spawned.Length < SLOTS)   ; never compare an array to None: a fatal cast error aborts the function
		OnInit()                                ; also grows the arrays of a save made with a smaller version
	EndIf
	EnsureStone()
	If Running
		InTick = False
		FriendlyFire(True)
		RegisterForMenu("Console")
		RegisterForSingleUpdate(1.0)
	EndIf
EndFunction

Event OnMenuOpen(String asMenu)
	{The console opening during a run ends it (every command, god mode included, goes through it).}
	If asMenu == "Console" && Running && !Busy
		EndNote = "The fog does not answer to the console. "
		EndRun(False)
	EndIf
EndEvent

Bool Function NeedsRestart()
	Return !Running && QuestVersion != None && (QuestVersion.GetValue() as Int) < QUEST_VERSION
EndFunction

Function PrepareRestart()
	{Called by the stone right before it stops and starts the quest: keeps the placed stone, stamps the version.}
	Persist.Revert()
	If StoneRef != None
		Persist.AddForm(StoneRef)
	EndIf
	QuestVersion.SetValue(QUEST_VERSION)
	HideBanner()
EndFunction

Function FriendlyFire(Bool abOff)
	{For the run, allies never turn on each other over stray hits; the settings are not saved, so a load re-applies.}
	If abOff
		If SavedFriendHits < 0
			SavedFriendHits = Game.GetGameSettingInt("iFriendHitCombatAllowed")
			SavedFriendHitsNC = Game.GetGameSettingInt("iFriendHitNonCombatAllowed")
		EndIf
		Game.SetGameSettingInt("iFriendHitCombatAllowed", FRIEND_HITS)
		Game.SetGameSettingInt("iFriendHitNonCombatAllowed", FRIEND_HITS)
	ElseIf SavedFriendHits >= 0
		Game.SetGameSettingInt("iFriendHitCombatAllowed", SavedFriendHits)
		Game.SetGameSettingInt("iFriendHitNonCombatAllowed", SavedFriendHitsNC)
		SavedFriendHits = -1
	EndIf
EndFunction

Function StoneActivated(ObjectReference akStone)
	If Busy
		Return
	EndIf
	If Running || PlayerRef.GetWorldSpace() == FogWoodWorld
		If LeaveMsg.Show() == 0
			If Running
				EndRun(False)
			Else
				ExitToStone()                   ; came in by other means (console): just the way out
			EndIf
		EndIf
	Else
		If EnterMsg.Show() == 0
			If PO3_SKSEFunctions.GetGodMode()
				Debug.MessageBox("The fog will not take an immortal. Turn god mode off first.")
			else
				StartRun()
			EndIf
		EndIf
	EndIf
EndFunction

Function StartRun()
	Busy = True
	Running = True
	WaveActive = False
	Wave = 0
	CorpseCount = 0
	LastTheme = None
	TraceBudget = TRACE_BUDGET
	If !Drops
		Drops = new ObjectReference[128]
		OldDrops = new ObjectReference[128]
	EndIf
	If !Chests
		Chests = new ObjectReference[32]
	EndIf
	If !LastX || !FarFor
		LastX = new Float[40]
		LastY = new Float[40]
		StillFor = new Int[40]
		FarFor = new Int[40]
	EndIf
	If !Doomed
		Doomed = new Actor[120]
	EndIf
	ChestCount = 0
	CacheUsed = new Bool[40]
	CurrentWave.SetValue(0)
	ArenaFaction.SetAlly(ArenaFaction, True, True)    ; the record says so too; members of one faction are not allies by default
	FriendlyFire(True)
	EndNote = ""
	RegisterForMenu("Console")                  ; curator, 2026-11-06: no console and no god mode during a run
	EPRank = PlayerRef.GetFactionRank(EPFaction)
	PlayerRef.RemoveFromFaction(EPFaction)
	PlayerRef.GetActorBase().SetEssential(True)
	PlayerRef.SetNoBleedoutRecovery(False)
	Game.FadeOutGame(True, True, 0.0, 1.0)
	Utility.Wait(1.0)
	PlayerRef.MoveTo(EntryMarker)
	Utility.Wait(1.0)
	Game.FadeOutGame(False, True, 0.0, 1.5)
	PlaceChests(CHESTS_AT_START)
	ShowBanner(OBJ_START)
	Debug.Trace("ZFW: run started")
	NextWaveAt = Utility.GetCurrentRealTime() + FIRST_WAVE_DELAY
	InTick = False
	Busy = False
	RegisterForSingleUpdate(1.0)
EndFunction

Function EndRun(Bool abDied)
	If !Running || Busy
		Return
	EndIf
	Busy = True
	Running = False
	WaveActive = False
	UnregisterForMenu("Console")
	HideBanner()
	Game.FadeOutGame(True, True, 0.0, 1.0)
	Utility.Wait(1.0)
	ClearSpawns()
	ClearCorpses()
	ClearDrops()
	ClearChests()
	FriendlyFire(False)
	PlayerRef.StopCombat()
	PlayerRef.RestoreActorValue("Health", 100000.0)
	PlayerRef.RestoreActorValue("Magicka", 100000.0)
	PlayerRef.RestoreActorValue("Stamina", 100000.0)
	EnsureStone()
	If StoneRef != None
		PlayerRef.MoveTo(StoneRef, 128.0, 0.0, 0.0)
	EndIf
	PlayerRef.AddToFaction(EPFaction)
	If EPRank > 0
		PlayerRef.SetFactionRank(EPFaction, EPRank)
	EndIf
	PlayerRef.GetActorBase().SetEssential(False)
	Utility.Wait(1.0)
	Game.FadeOutGame(False, True, 0.0, 1.5)
	DeleteDoomed()                              ; the bodies ClearSpawns()/ClearCorpses() disabled two seconds ago
	Int best = BestWave.GetValue() as Int
	If abDied
		Debug.MessageBox(EndNote + "The fog releases you. You fell on wave " + Wave + ".\nBest: wave " + best + ".")
	Else
		Debug.MessageBox(EndNote + "You leave the Fog Wood on wave " + Wave + ".\nBest: wave " + best + ".")
	EndIf
	EndNote = ""
	CurrentWave.SetValue(0)
	Busy = False
EndFunction

Function ExitToStone()
	Busy = True
	Game.FadeOutGame(True, True, 0.0, 1.0)
	Utility.Wait(1.0)
	EnsureStone()
	If StoneRef != None
		PlayerRef.MoveTo(StoneRef, 128.0, 0.0, 0.0)
	EndIf
	Utility.Wait(1.0)
	Game.FadeOutGame(False, True, 0.0, 1.5)
	Busy = False
EndFunction

Event OnUpdate()
	If !Running
		EnsureStone()
		Return
	EndIf
	RegisterForSingleUpdate(1.0)                ; FIRST: an error anywhere below used to end the loop, and with it the waves
	                                            ; (a tester cleared wave 2 and nothing more came, 2026-11-07)
	Float now = Utility.GetCurrentRealTime()
	If InTick
		If now - TickStarted < TICK_TIMEOUT
			Return                              ; the previous tick is still running (placing a wave takes seconds)
		EndIf
		Debug.Trace("ZFW: a tick did not finish in " + TICK_TIMEOUT + " s; the loop takes over")
	EndIf
	InTick = True                               ; Papyrus runs every event on its own thread: without this flag the tick
	TickStarted = now                           ; that arrived while SpawnWave was still placing saw no active wave and
	Tick()                                      ; started a second theme on top of the first (curator, 2026-11-09)
	InTick = False
EndEvent

Function Tick()
	{One second of the run. Never two at once: OnUpdate's InTick guard.}
	DeleteDoomed()                              ; the bodies ClearCorpses() disabled on the previous tick
	If Busy
		Return
	EndIf
	If PlayerRef.GetWorldSpace() != FogWoodWorld
		EndRun(False)                           ; the player left by other means
		Return
	EndIf
	If PO3_SKSEFunctions.GetGodMode()
		EndNote = "The fog will not take an immortal. "
		EndRun(False)
		Return
	EndIf
	If Outside(PlayerRef)
		Debug.Notification("The fog turns you back.")
		PlayerRef.MoveTo(EntryMarker)
	EndIf
	If PlayerRef.IsBleedingOut() || PlayerRef.GetActorValue("Health") <= 0.0
		EndRun(True)                            ; fallback for the alias's OnEnterBleedout (Enderal has no health regen, so nobody gets up)
		Return
	EndIf
	If WaveActive
		Int alive = ProcessDeaths()
		If alive == 0
			WaveActive = False
			ShowBanner(OBJ_CLEARED)
			If Wave % BOSS_EVERY == 0
				PlaceChests(CHESTS_PER_BOSS)
				Debug.Notification("The fog has left new caches in the wood.")
			EndIf
			NextWaveAt = Utility.GetCurrentRealTime() + NEXT_WAVE_DELAY
		ElseIf alive <= LAST_FEW && Utility.GetCurrentRealTime() - LastKillAt > NO_KILL_SECONDS
			GatherLastFew(alive)
			LastKillAt = Utility.GetCurrentRealTime()
		EndIf
	ElseIf Utility.GetCurrentRealTime() >= NextWaveAt
		ClearCorpses()
		RotateDrops()
		SpawnWave(Wave + 1)
	EndIf
EndFunction

Int Function ProcessDeaths()
	{Counts the living; a dead spawn is stripped, drops its loot once, leaves its alias and joins the corpse list;
	 a live one is kept on the player.}
	Int alive = 0
	Int i = 0
	While i < Spawned.Length
		Actor a = Spawned[i]
		If a != None
			If a.IsDead()
				LastKillAt = Utility.GetCurrentRealTime()
				GiveDrops(a, SpawnedElite[i], SpawnedBoss[i])
				ClearSlot(i)
				If CorpseCount < Corpses.Length
					Corpses[CorpseCount] = a
					CorpseCount += 1
				EndIf
				Spawned[i] = None
			Else
				alive += 1
				If a.GetActorValue("Health") > 0.0 ; dying: StartCombat on it only logs an error
					If Outside(a)                   ; knocked through the edge wall: the player cannot follow
						Relocate(a)
					EndIf
					Refocus(a)
					WatchStuck(a, i)
					WatchFar(a, i)
				EndIf
			EndIf
		EndIf
		i += 1
	EndWhile
	Return alive
EndFunction

Function GiveDrops(Actor akCorpse, Bool abElite, Bool abBoss)
	{Locks the corpse against looting, then drops the loot on the ground beside it, where it can be picked up without
	 opening a corpse in the middle of a horde. RemoveAllItems did the locking in the first builds and took the worn
	 armour with it: dismembered bandits lay naked (curator, 2026-11-06; traced to this line by the DF session).}
	akCorpse.BlockActivation(True)
	If abBoss || abElite || Utility.RandomFloat(0.0, 1.0) < AMMO_CHANCE
		Int n = Utility.RandomInt(4, 8)
		If abBoss
			n = 12
		EndIf
		Form shot = PO3_SKSEFunctions.GetEquippedAmmo(PlayerRef)
		If shot != None
			Drop(akCorpse, shot, n)
		EndIf
		Form bullet = PistolBullet()
		If bullet != None && bullet != shot
			Drop(akCorpse, bullet, n)
		EndIf
	EndIf
	Int tier = PotionTier()
	If abBoss
		Drop(akCorpse, HealthPotions.GetAt(tier), 2)
		Drop(akCorpse, Ambrosia, 1)
		Drop(akCorpse, ManaPotions.GetAt(tier), 1)
	ElseIf abElite
		Drop(akCorpse, HealthPotions.GetAt(tier), 1)
		If Utility.RandomFloat(0.0, 1.0) < 0.5
			Drop(akCorpse, Ambrosia, 1)
		EndIf
		If Utility.RandomFloat(0.0, 1.0) < 0.3
			Drop(akCorpse, ManaPotions.GetAt(tier), 1)
		EndIf
	ElseIf Utility.RandomFloat(0.0, 1.0) < REGULAR_POTION_CHANCE
		Drop(akCorpse, HealthPotions.GetAt(tier), 1)
	EndIf
EndFunction

Function Drop(ObjectReference akCorpse, Form akItem, Int aiCount)
	{Puts the item into the corpse and drops it out onto the ground; the dropped ref is remembered so the wood
	 is swept two waves later.}
	If akItem == None
		Return
	EndIf
	akCorpse.AddItem(akItem, aiCount, True)
	ObjectReference dropped = akCorpse.DropObject(akItem, aiCount)
	If dropped != None && Drops && DropCount < Drops.Length
		Drops[DropCount] = dropped
		DropCount += 1
	EndIf
EndFunction

Int Function PotionTier()
	Int t = (Wave - 1) / POTION_TIER_WAVES
	If t < 0
		t = 0
	EndIf
	If t > HealthPotions.GetSize() - 1
		t = HealthPotions.GetSize() - 1
	EndIf
	Return t
EndFunction

Form Function PistolBullet()
	{The Flintlock Overhaul's bullet while the player carries any of its pistols (list 0x802).}
	FormList pistols = Game.GetFormFromFile(0x802, FLINTLOCK) as FormList
	If pistols != None && PlayerRef.GetItemCount(pistols) > 0
		Return Game.GetFormFromFile(0x800, FLINTLOCK)
	EndIf
	Return None
EndFunction

Function SpawnWave(Int aiWave)
	Wave = aiWave
	CurrentWave.SetValue(aiWave)
	If aiWave > BestWave.GetValue() as Int
		BestWave.SetValue(aiWave)
	EndIf
	FormList theme = PickTheme(TierFor(aiWave))
	FormList regulars = theme.GetAt(0) as FormList
	FormList elites = theme.GetAt(1) as FormList
	FormList bosses = theme.GetAt(2) as FormList
	String shown = theme.GetAt(3).GetName()
	Float pack = (theme.GetAt(4) as GlobalVariable).GetValue()
	Bool bossWave = (aiWave % BOSS_EVERY) == 0
	Int count = FIRST_WAVE + WAVE_STEP * (aiWave - 1)
	If count > MAX_SPAWNS
		count = MAX_SPAWNS
	EndIf
	count = (count * pack) as Int
	If count < MIN_PACK
		count = MIN_PACK
	EndIf
	If bossWave
		count = 1 + count / 2
	EndIf
	Int nElites = 1 + (aiWave - 1) / ELITE_EVERY
	If nElites > MAX_ELITES
		nElites = MAX_ELITES
	EndIf
	If nElites > count - 1
		nElites = count - 1
	EndIf
	Int[] order = ShuffledMarkers()
	Int nMarkers = SpawnMarkers.Length
	String bossName = ""
	Int i = 0
	While i < count && i < Spawned.Length
		If !Running || Busy
			Return                              ; the run ended under us (alias bleedout, console): place no more
		EndIf
		ObjectReference marker = SpawnMarkers[order[i % nMarkers]]
		Bool boss = bossWave && i == 0
		Bool elite = !boss && i >= count - nElites
		FormList pool = regulars
		If boss
			pool = bosses
		ElseIf elite
			pool = elites
		EndIf
		ActorBase base = pool.GetAt(Utility.RandomInt(0, pool.GetSize() - 1)) as ActorBase
		; placed DISABLED: a live spawn runs its own AI with its own factions at once, and two species next
		; to each other were already fighting before Prepare reached them (a fight survives the faction change)
		Actor a = marker.PlaceAtMe(base, 1, False, True) as Actor
		If a != None
			If i >= nMarkers                    ; second and third spawn on a marker: spread them out
				a.SetPosition(marker.GetPositionX() + Utility.RandomFloat(-SPREAD, SPREAD), marker.GetPositionY() + Utility.RandomFloat(-SPREAD, SPREAD), marker.GetPositionZ())
			EndIf
			Prepare(a, elite, boss)
			If boss
				bossName = a.GetDisplayName()
			EndIf
			ReferenceAlias slot = GetAlias(i + 1) as ReferenceAlias
			If slot != None
				slot.ForceRefTo(a)
			EndIf
			a.Enable()
			a.IgnoreFriendlyHits()                ; again once the actor runs: set on a disabled actor it may not have taken
			a.RestoreActorValue("Health", 100000.0)
			a.StartCombat(PlayerRef)
			Spawned[i] = a
			SpawnedElite[i] = elite
			SpawnedBoss[i] = boss
			LastX[i] = a.GetPositionX()
			LastY[i] = a.GetPositionY()
			StillFor[i] = 0
			FarFor[i] = 0
		EndIf
		i += 1
	EndWhile
	If !Running || Busy
		Return
	EndIf
	WaveActive = True
	LastKillAt = Utility.GetCurrentRealTime()
	If bossWave
		WaveSize.SetValue(count - 1)
	Else
		WaveSize.SetValue(count)
	EndIf
	Int idx = Themes.Find(theme)
	If idx >= 0 && bossWave
		ShowBanner(OBJ_BOSS0 + idx)
	ElseIf idx >= 0
		ShowBanner(OBJ_WAVE0 + idx)
	ElseIf bossWave
		Debug.Notification("Wave " + aiWave + ": " + bossName + " leads " + (count - 1) + " " + shown + ".")
	Else
		Debug.Notification("Wave " + aiWave + ": " + count + " " + shown + ", " + nElites + " elite.")
	EndIf
EndFunction

Function PlaceChests(Int aiCount)
	{Fogbound Caches: chests on random cache markers not used yet this run (every marker is a clear lattice vertex
	 at ground height), stocked with potions of the wave's tier, and remembered so the run's end sweeps them.}
	If !CacheUsed || CacheUsed.Length != CacheMarkers.Length
		CacheUsed = new Bool[40]
	EndIf
	Int i = 0
	While i < aiCount && ChestCount < Chests.Length
		Int pick = Utility.RandomInt(0, CacheMarkers.Length - 1)
		Int tries = 0
		While CacheUsed[pick] && tries < CacheMarkers.Length
			pick = (pick + 1) % CacheMarkers.Length
			tries += 1
		EndWhile
		ObjectReference marker = CacheMarkers[pick]
		ObjectReference c = marker.PlaceAtMe(ChestBase, 1, False, True)
		If c != None
			c.SetPosition(marker.GetPositionX(), marker.GetPositionY(), marker.GetPositionZ())
			c.SetAngle(0.0, 0.0, marker.GetAngleZ())
			StockChest(c)
			c.Enable()
			Debug.Trace("ZFW: cache " + ChestCount + " at " + c.GetPositionX() + ", " + c.GetPositionY() + ", " + c.GetPositionZ())
			Chests[ChestCount] = c
			ChestCount += 1
			CacheUsed[pick] = True
		EndIf
		i += 1
	EndWhile
EndFunction

Function StockChest(ObjectReference akChest)
	{Health potions of the wave's tier, a chance of mana, stamina and Ambrosia, and one or two resistance potions.}
	Int tier = PotionTier()
	akChest.AddItem(HealthPotions.GetAt(tier), Utility.RandomInt(1, 2), True)
	If Utility.RandomFloat(0.0, 1.0) < 0.6
		akChest.AddItem(ManaPotions.GetAt(tier), 1, True)
	EndIf
	If Utility.RandomFloat(0.0, 1.0) < 0.4
		akChest.AddItem(StaminaPotion, 1, True)
	EndIf
	If Utility.RandomFloat(0.0, 1.0) < 0.4
		akChest.AddItem(Ambrosia, 1, True)
	EndIf
	Int n = Utility.RandomInt(1, 2)
	While n > 0
		akChest.AddItem(CachePotions.GetAt(Utility.RandomInt(0, CachePotions.GetSize() - 1)), 1, True)
		n -= 1
	EndWhile
EndFunction

Function ClearChests()
	{Deletes the caches. The fog's own stock goes with them; anything else in them is the player's, put there during
	 the run, and goes back to the player (a tester lost items left in the wood, 2026-11-07).}
	Int returned = 0
	Int i = 0
	While i < ChestCount
		If Chests[i] != None
			RemoveStock(Chests[i])
			If Chests[i].GetNumItems() > 0
				returned += Chests[i].GetNumItems()
				Chests[i].RemoveAllItems(PlayerRef, False, True)
			EndIf
			Chests[i].Disable()
			Chests[i].Delete()
			Chests[i] = None
		EndIf
		i += 1
	EndWhile
	ChestCount = 0
	If returned > 0
		Debug.Notification("The fog returns what you left in its caches.")
	EndIf
EndFunction

Function RemoveStock(ObjectReference akChest)
	{Takes every potion kind StockChest can put in a cache back out of it.}
	Int k = 0
	While k < HealthPotions.GetSize()
		akChest.RemoveItem(HealthPotions.GetAt(k), 999, True)
		k += 1
	EndWhile
	k = 0
	While k < ManaPotions.GetSize()
		akChest.RemoveItem(ManaPotions.GetAt(k), 999, True)
		k += 1
	EndWhile
	k = 0
	While k < CachePotions.GetSize()
		akChest.RemoveItem(CachePotions.GetAt(k), 999, True)
		k += 1
	EndWhile
	akChest.RemoveItem(StaminaPotion, 999, True)
	akChest.RemoveItem(Ambrosia, 999, True)
EndFunction

Function ShowBanner(Int aiObjective)
	{Shows one quest objective (the large centred quest-update text) and hides the one before it, so the journal
	 never piles them up. The <Global=...> tags read the quest instance's SNAPSHOT of each global, refreshed only by
	UpdateCurrentInstanceGlobal (every SureAI counter objective calls it); without it the tag stays unreplaced and the
	 HUD, a Scaleform text field, swallows it as markup with the rest of the line: the first test read "Wave ...".}
	UpdateCurrentInstanceGlobal(CurrentWave)
	UpdateCurrentInstanceGlobal(WaveSize)
	If ShownObjective >= 0 && ShownObjective != aiObjective
		SetObjectiveDisplayed(ShownObjective, False)
	EndIf
	SetObjectiveDisplayed(aiObjective, True, True)
	ShownObjective = aiObjective
EndFunction

Function HideBanner()
	If ShownObjective >= 0
		SetObjectiveDisplayed(ShownObjective, False)
	EndIf
	ShownObjective = -1
EndFunction

FormList Function PickTheme(FormList akTier)
	{A random theme of the tier, not the one just fought when the tier has more than one.}
	Int n = akTier.GetSize()
	FormList theme = akTier.GetAt(Utility.RandomInt(0, n - 1)) as FormList
	If n > 1 && theme == LastTheme
		theme = akTier.GetAt(Utility.RandomInt(0, n - 1)) as FormList
	EndIf
	LastTheme = theme
	Return theme
EndFunction

Function Prepare(Actor akActor, Bool abElite, Bool abBoss)
	{One faction for every spawn, friendly hits ignored, so they fight the player and not each other; no fleeing;
	 elites and bosses named and tougher.}
	akActor.RemoveFromAllFactions()
	akActor.AddToFaction(ArenaFaction)           ; the faction is Ally to ITSELF: members of one faction are not allies by default
	akActor.IgnoreFriendlyHits()
	akActor.SetActorValue("Aggression", 1.0)     ; enemies only (the player, through the faction); 2 attacks neutrals too
	akActor.SetActorValue("Confidence", 4.0)
	akActor.SetActorValue("Assistance", 0.0)     ; never join another spawn's fight: a stray hit stays a stray hit
	Float mult = 1.0
	If abBoss
		mult = BOSS_HEALTH
		akActor.SetDisplayName(akActor.GetDisplayName() + " of the Fog", True)
	ElseIf abElite
		mult = ELITE_HEALTH
		akActor.SetDisplayName("Elite " + akActor.GetDisplayName(), True)
	EndIf
	If mult != 1.0
		akActor.SetActorValue("Health", akActor.GetBaseActorValue("Health") * mult)
	EndIf
EndFunction

Function WatchStuck(Actor akActor, Int aiIndex)
	{Every second: a spawn that has not moved for STUCK_SECONDS while out of reach of the player is logged and put
	 back on a spawn marker, in combat with the player.}
	Float x = akActor.GetPositionX()
	Float y = akActor.GetPositionY()
	Float dx = x - LastX[aiIndex]
	Float dy = y - LastY[aiIndex]
	LastX[aiIndex] = x
	LastY[aiIndex] = y
	If dx * dx + dy * dy < STUCK_MOVE * STUCK_MOVE && akActor.GetDistance(PlayerRef) > STUCK_RANGE && !akActor.IsBleedingOut()
		StillFor[aiIndex] = StillFor[aiIndex] + 1
		If StillFor[aiIndex] >= STUCK_SECONDS
			StillFor[aiIndex] = 0
			If TraceBudget > 0
				TraceBudget -= 1
				Debug.Trace("ZFW stuck: " + akActor.GetDisplayName() + " (" + akActor + ") base " + akActor.GetBaseObject() + " at " + x + ", " + y + ", " + akActor.GetPositionZ() + "; combat state " + akActor.GetCombatState() + ", target " + akActor.GetCombatTarget() + ", weapon " + akActor.GetEquippedWeapon() + " / " + akActor.GetEquippedWeapon(True) + ", health " + akActor.GetActorValue("Health") + ", distance " + akActor.GetDistance(PlayerRef) + ", alerted " + akActor.IsAlerted() + ", AI " + akActor.IsAIEnabled() + "; moved onto a spawn marker")
			EndIf
			Relocate(akActor)
		EndIf
	Else
		StillFor[aiIndex] = 0
	EndIf
EndFunction

Function WatchFar(Actor akActor, Int aiIndex)
	{Every second: a spawn out of reach for FAR_SECONDS is brought to the player.}
	If akActor.GetDistance(PlayerRef) > FAR_RANGE
		FarFor[aiIndex] = FarFor[aiIndex] + 1
		If FarFor[aiIndex] >= FAR_SECONDS
			FarFor[aiIndex] = 0
			Relocate(akActor)
		EndIf
	Else
		FarFor[aiIndex] = 0
	EndIf
EndFunction

Bool Function Outside(ObjectReference akRef)
	Return Math.Abs(akRef.GetPositionX()) > BOUND || Math.Abs(akRef.GetPositionY()) > BOUND
EndFunction

Function GatherLastFew(Int aiAlive)
	{The wave's last few, out of reach for NO_KILL_SECONDS, are brought to the player.}
	Int i = 0
	While i < Spawned.Length
		Actor a = Spawned[i]
		If a != None && a.GetActorValue("Health") > 0.0 && a.GetDistance(PlayerRef) > NO_KILL_RANGE
			If TraceBudget > 0
				TraceBudget -= 1
				Debug.Trace("ZFW: gathering one of the last " + aiAlive + " (no kill for " + NO_KILL_SECONDS + " s)")
			EndIf
			Relocate(a)
		EndIf
		i += 1
	EndWhile
EndFunction

ObjectReference Function MarkerNearPlayer()
	{The cache or spawn marker nearest the player that is at least NEAR_MIN away: a clear lattice vertex at ground
	 height, so nothing lands in a tree.}
	ObjectReference best = None
	Float bestD = 1000000.0
	Int i = 0
	While i < CacheMarkers.Length
		Float d = CacheMarkers[i].GetDistance(PlayerRef)
		If d >= NEAR_MIN && d < bestD
			best = CacheMarkers[i]
			bestD = d
		EndIf
		i += 1
	EndWhile
	i = 0
	While i < SpawnMarkers.Length
		Float d = SpawnMarkers[i].GetDistance(PlayerRef)
		If d >= NEAR_MIN && d < bestD
			best = SpawnMarkers[i]
			bestD = d
		EndIf
		i += 1
	EndWhile
	If best == None
		best = SpawnMarkers[Utility.RandomInt(0, SpawnMarkers.Length - 1)]
	EndIf
	Return best
EndFunction

Function Relocate(Actor akActor)
	{Moves a lost or stuck spawn to the clear marker nearest the player and restarts it on them.}
	ObjectReference marker = MarkerNearPlayer()
	If TraceBudget > 0
		TraceBudget -= 1
		Debug.Trace("ZFW: brought " + akActor.GetDisplayName() + " (" + akActor + ") from " + akActor.GetDistance(PlayerRef) + " units to " + marker.GetDistance(PlayerRef) + " units off the player")
	EndIf
	akActor.MoveTo(marker)
	akActor.StopCombat()
	akActor.StartCombat(PlayerRef)
EndFunction

Function Refocus(Actor akActor)
	{Every second: a spawn that is not in combat, is searching, or fights anything but the player is restarted
	 on the player (curator: "always chasing the player"). StartCombat hands the actor the player's current
	 position, so the fog never loses them. A spawn found on another target is logged (Papyrus log, budgeted).}
	Actor target = akActor.GetCombatTarget()
	If akActor.GetCombatState() != 1 || target != PlayerRef
		If target != None && target != PlayerRef && TraceBudget > 0
			TraceBudget -= 1
			Debug.Trace("ZFW target: " + akActor.GetDisplayName() + " (" + akActor + ") targets " + target.GetDisplayName() + " (" + target + "): hostile " + akActor.IsHostileToActor(target) + "/" + target.IsHostileToActor(akActor) + ", arena faction " + akActor.IsInFaction(ArenaFaction) + "/" + target.IsInFaction(ArenaFaction) + ", relationship " + akActor.GetRelationshipRank(target))
		EndIf
		If akActor.GetCombatState() != 0
			akActor.StopCombat()
		EndIf
		akActor.StartCombat(PlayerRef)
	EndIf
EndFunction

Function SpawnHit(Actor akVictim, Actor akAggressor, Form akSource, Projectile akProjectile)
	{From ZFW_SpawnAlias: a spawn was hit by something that is not the player. Logged with the facts that decide
	 whether the engine should have treated it as a friendly hit.}
	If TraceBudget <= 0
		Return
	EndIf
	TraceBudget -= 1
	Debug.Trace("ZFW hit: " + akAggressor.GetDisplayName() + " (" + akAggressor + ") hit " + akVictim.GetDisplayName() + " (" + akVictim + ") with " + akSource + " projectile " + akProjectile + "; aggressor in arena faction " + akAggressor.IsInFaction(ArenaFaction) + ", aggressor target " + akAggressor.GetCombatTarget() + ", victim hostile to aggressor " + akVictim.IsHostileToActor(akAggressor) + ", victim combat state " + akVictim.GetCombatState())
EndFunction

FormList Function TierFor(Int aiWave)
	If aiWave <= 3
		Return Tier1
	ElseIf aiWave <= 6
		Return Tier2
	ElseIf aiWave <= 9
		Return Tier3
	ElseIf aiWave <= 12
		Return Tier4
	EndIf
	Return Tier5
EndFunction

Int[] Function ShuffledMarkers()
	Int n = SpawnMarkers.Length
	Int[] order = new Int[12]
	Int i = 0
	While i < n
		order[i] = i
		i += 1
	EndWhile
	i = n - 1
	While i > 0
		Int j = Utility.RandomInt(0, i)
		Int t = order[i]
		order[i] = order[j]
		order[j] = t
		i -= 1
	EndWhile
	Return order
EndFunction

Function ClearSlot(Int aiIndex)
	ReferenceAlias slot = GetAlias(aiIndex + 1) as ReferenceAlias
	If slot != None
		slot.Clear()
	EndIf
EndFunction

Function ClearSpawns()
	Int i = 0
	While i < Spawned.Length
		Actor a = Spawned[i]
		If a != None
			ClearSlot(i)
			Doom(a)
			Spawned[i] = None
		EndIf
		i += 1
	EndWhile
EndFunction

Function ClearCorpses()
	Int i = 0
	While i < CorpseCount
		If Corpses[i] != None
			Doom(Corpses[i])
			Corpses[i] = None
		EndIf
		i += 1
	EndWhile
	CorpseCount = 0
EndFunction

Function Doom(Actor akBody)
	{Disables the body now and queues its Delete() for a later tick (DeleteDoomed). Disable() + Delete() in one frame
	 freed a corpse's 3D root under a queued weapon re-hang job (SkyrimSE.exe+0FDDB2D, a player's crash in the arena
	 on 2026-11-07); whether a second's gap is enough is unverified. A full queue deletes at once, as before.}
	akBody.Disable()
	If !Doomed
		Doomed = new Actor[120]
	EndIf
	If DoomedCount < Doomed.Length
		Doomed[DoomedCount] = akBody
		DoomedCount += 1
	Else
		akBody.Delete()
	EndIf
EndFunction

Function DeleteDoomed()
	{Deletes the bodies Doom() disabled on an earlier tick.}
	If !Doomed
		Return
	EndIf
	Int i = 0
	While i < DoomedCount
		If Doomed[i] != None
			Doomed[i].Delete()
			Doomed[i] = None
		EndIf
		i += 1
	EndWhile
	DoomedCount = 0
EndFunction

Function RotateDrops()
	{At each new wave: what was dropped two waves ago and never picked up is swept; last wave's drops get one
	 more wave on the ground.}
	Int i = 0
	While i < OldDropCount
		If OldDrops[i] != None
			OldDrops[i].Disable()
			OldDrops[i].Delete()
			OldDrops[i] = None
		EndIf
		i += 1
	EndWhile
	ObjectReference[] swap = OldDrops
	OldDrops = Drops
	OldDropCount = DropCount
	Drops = swap
	DropCount = 0
EndFunction

Function ClearDrops()
	RotateDrops()
	RotateDrops()
EndFunction
